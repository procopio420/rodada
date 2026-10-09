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
    required_capability = Capability.VENUE_CONFIGURE

    def get(self, request):
        return Response(
            {
                "results": list(
                    MerchantConnection.objects.filter(
                        venue_id=request.actor_context.venue_id
                    ).values("id", "provider", "merchant_code", "active", "capabilities")
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
            return Response({"authorization_url": begin_connection(request.actor_context)})
        except ProviderServiceError as error:
            return error_response(error)
        except (KeyError, ValueError, OSError):
            return Response({"code": "MERCHANT_CONNECTION_UNVERIFIED"}, status=503)

    def delete(self, request):
        try:
            disconnect_connection(
                connection_id=request.data.get("connection_id"), actor=request.actor_context
            )
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
