from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability, RequireRecentReauthentication
from modules.ledger.models import Payment, Refund

from .models import ProviderRefundRequest
from .refunds import reconcile_provider_refund, request_provider_refund
from .registry import provider_for_venue
from .services import ProviderServiceError
from .views import error_response


class IntegratedRefundView(APIView):
    permission_classes = (IsAuthenticated, RequireCapability, RequireRecentReauthentication)
    required_capability = Capability.REFUND_CREATE

    def post(self, request, payment_id):
        payment = Payment.objects.filter(
            pk=payment_id, tab__venue_id=request.actor_context.venue_id
        ).first()
        if payment is None:
            return Response({"code": "PAYMENT_NOT_FOUND"}, status=404)
        try:
            provider = provider_for_venue(
                request.actor_context.venue_id, payment.method, payment.provider
            )
            refund = request_provider_refund(
                payment_id=payment.pk,
                amount_cents=request.data.get("amount_cents"),
                key=request.data.get("idempotency_key", ""),
                reason=request.data.get("reason", ""),
                actor=request.actor_context,
                provider=provider,
            )
        except ProviderServiceError as error:
            return error_response(error)
        except (ValueError, KeyError, OSError):
            return Response({"code": "REFUND_CONFIRMATION_PENDING"}, status=503)
        return Response({"id": str(refund.pk), "status": refund.status}, status=202)


class IntegratedRefundReconcileView(IntegratedRefundView):
    def post(self, request, refund_id):
        refund = (
            Refund.objects.select_related("payment")
            .filter(pk=refund_id, payment__tab__venue_id=request.actor_context.venue_id)
            .first()
        )
        if refund is None:
            return Response({"code": "REFUND_NOT_FOUND"}, status=404)
        try:
            refund = reconcile_provider_refund(
                refund_id=refund.pk,
                actor=request.actor_context,
                provider=provider_for_venue(
                    request.actor_context.venue_id, refund.payment.method, refund.payment.provider
                ),
            )
        except ProviderServiceError as error:
            return error_response(error)
        except (ProviderRefundRequest.DoesNotExist, ValueError, KeyError, OSError):
            return Response({"code": "REFUND_UNVERIFIED"}, status=409)
        return Response({"id": str(refund.pk), "status": refund.status})
