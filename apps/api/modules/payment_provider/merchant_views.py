import hashlib
from urllib.parse import parse_qs, urlparse

from django.core import signing
from django.http import HttpResponse
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability, RequireRecentReauthentication

from .merchant_services import begin_connection, complete_connection, disconnect_connection
from .models import DeviceAuthorization, MerchantConnection
from .services import ProviderServiceError
from .views import error_response


class MerchantConnectionView(APIView):
    permission_classes = (IsAuthenticated, RequireCapability, RequireRecentReauthentication)
    required_capability = Capability.PAYMENT_PROVIDER_CONFIGURE

    def get(self, request):
        return Response(
            {
                "results": list(
                    MerchantConnection.objects.filter(
                        venue_id=request.actor_context.venue_id
                    ).values(
                        "id",
                        "provider",
                        "merchant_code",
                        "active",
                        "capabilities",
                        "scopes",
                        "token_expires_at",
                        "disconnected_at",
                    )
                )
            }
        )

    def post(self, request):
        try:
            if request.data.get("code"):
                connection = complete_connection(
                    actor=request.actor_context,
                    state=request.data.get("state", ""),
                    code=request.data["code"],
                )
                return Response(
                    {"id": str(connection.pk), "merchant_code": connection.merchant_code}
                )
            url = begin_connection(request.actor_context)
            state = parse_qs(urlparse(url).query)["state"][0]
            response = Response({"authorization_url": url})
            response.set_signed_cookie(
                "rodada_payment_oauth",
                f"{request.auth.pk}:{hashlib.sha256(state.encode()).hexdigest()}",
                salt="payment-oauth",
                max_age=600,
                secure=True,
                httponly=True,
                samesite="Lax",
                path="/payments/merchant-connections/callback/",
            )
            response["Cache-Control"] = "no-store"
            return response
        except ProviderServiceError as error:
            return error_response(error)
        except (KeyError, ValueError, OSError):
            return Response({"code": "MERCHANT_CONNECTION_UNVERIFIED"}, status=503)

    def delete(self, request):
        try:
            disconnect_connection(
                connection_id=request.data.get("connection_id"), actor=request.actor_context
            )
        except ProviderServiceError as error:
            return error_response(error)
        except (MerchantConnection.DoesNotExist, ValueError):
            return Response({"code": "MERCHANT_CONNECTION_NOT_FOUND"}, status=404)
        return Response(status=204)


class PaymentDeviceAuthorizationView(MerchantConnectionView):
    def post(self, request):
        from modules.access.models import DeviceRegistration, VenueStaffMembership
        from modules.audit.services import record_audit_event

        connection = MerchantConnection.objects.filter(
            pk=request.data.get("connection_id"),
            venue_id=request.actor_context.venue_id,
            active=True,
        ).first()
        device = DeviceRegistration.objects.filter(
            pk=request.data.get("device_id"),
            venue_id=request.actor_context.venue_id,
            trust_state="TRUSTED",
        ).first()
        membership = VenueStaffMembership.objects.filter(
            staff_member_id=request.data.get("staff_id"),
            venue_id=request.actor_context.venue_id,
            status="ACTIVE",
        ).first()
        if connection is None or device is None or membership is None:
            return Response({"code": "PAYMENT_DEVICE_UNAUTHORIZED"}, status=403)
        authorization, _ = DeviceAuthorization.objects.update_or_create(
            connection=connection,
            device=device,
            staff=membership.staff_member,
            defaults={"active": request.data.get("active") is True},
        )
        record_audit_event(
            actor=request.actor_context,
            event_type="payment.device_authorization_changed",
            entity_type="DeviceAuthorization",
            entity_id=str(authorization.pk),
            metadata={"active": authorization.active},
        )
        return Response({"id": authorization.pk, "active": authorization.active})


class OAuthCallbackAuthentication(BaseAuthentication):
    """Only this endpoint accepts the browser-bound, ten-minute OAuth cookie."""

    def authenticate(self, request):
        from modules.access.context import ActorContext
        from modules.access.models import StaffSession
        from modules.access.services import _session_failure

        try:
            binding = request.get_signed_cookie(
                "rodada_payment_oauth", salt="payment-oauth", max_age=600
            )
            session_id, state_hash = binding.split(":", 1)
            state = request.query_params.get("state", "")
            import secrets

            if not state or not secrets.compare_digest(
                state_hash, hashlib.sha256(state.encode()).hexdigest()
            ):
                raise ValueError("State mismatch")
            session = StaffSession.objects.select_related(
                "membership", "staff_member", "device"
            ).get(pk=session_id)
            if _session_failure(session):
                raise ValueError("Session unavailable")
        except (KeyError, ValueError, signing.BadSignature, StaffSession.DoesNotExist) as error:
            raise AuthenticationFailed("Autorização inválida ou expirada.") from error
        request.actor_context = ActorContext.from_session(session)
        return session.staff_member, session


class MerchantOAuthCallbackView(MerchantConnectionView):
    authentication_classes = (OAuthCallbackAuthentication,)
    http_method_names = ("get", "options")

    def get(self, request):
        from .merchant_services import consume_authorization

        state = request.query_params.get("state", "")
        try:
            if request.query_params.get("error"):
                consume_authorization(actor=request.actor_context, state=state)
                message = "Conexão não autorizada. Volte ao Rodada para iniciar novamente."
            elif request.query_params.get("code"):
                complete_connection(
                    actor=request.actor_context, state=state, code=request.query_params["code"]
                )
                message = "Estabelecimento conectado. Volte ao Rodada. A habilitação de pagamentos depende do provedor."
            else:
                raise ValueError("Missing authorization code")
            response = HttpResponse(message, content_type="text/plain; charset=utf-8")
        except (ProviderServiceError, KeyError, ValueError, OSError):
            response = HttpResponse(
                "Conexão não verificada. Volte ao Rodada para iniciar novamente.",
                status=409,
                content_type="text/plain; charset=utf-8",
            )
        response.delete_cookie(
            "rodada_payment_oauth", path="/payments/merchant-connections/callback/", samesite="Lax"
        )
        response["Cache-Control"] = "no-store"
        response["Referrer-Policy"] = "no-referrer"
        return response
