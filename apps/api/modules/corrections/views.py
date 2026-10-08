from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability, RequireRecentReauthentication
from modules.corrections.models import CorrectionKind
from modules.corrections.services import (
    CorrectionServiceError,
    cancel_before_fulfillment,
    settle_refund_required_cancellation,
)
from modules.ledger.services import LedgerServiceError, reverse_open_responsibility, totals
from modules.ordering.models import OrderItem


class OrderItemCancelView(APIView):
    """The only staff mutation which can cancel a confirmed order item."""

    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.ORDER_CORRECT

    def post(self, request, item_id):
        try:
            correction = cancel_before_fulfillment(
                item_id=item_id,
                kind=request.data.get("kind", CorrectionKind.CANCEL_ITEM),
                reason_code=request.data.get("reason_code", ""),
                reason_text=request.data.get("reason_text", ""),
                idempotency_key=request.data.get("idempotency_key", ""),
                actor=request.actor_context,
                financial_reversal_hook=reverse_open_responsibility,
                record_paid_request=True,
            )
        except CorrectionServiceError as error:
            payload = {"code": error.code, "message": error.message}
            if error.details:
                payload.update(error.details)
            return Response(payload, status=error.status_code)
        except LedgerServiceError as error:
            return Response({"code": error.code, "message": error.message}, status=error.status_code)

        item = OrderItem.objects.select_related("order__tab").get(pk=item_id)
        payload = {
            "id": str(correction.id),
            "status": correction.status,
            "financial_disposition": correction.financial_disposition,
            "financial_adjustment_id": (
                str(correction.financial_adjustment_id) if correction.financial_adjustment_id else None
            ),
            "order_item_id": str(item.id),
            "order_item_state": item.state,
            **totals(item.order.tab),
        }
        if correction.financial_disposition == "REFUND_REQUIRED":
            return Response(payload, status=200 if getattr(correction, "_idempotency_replay", False) else 202)
        return Response(payload, status=200 if getattr(correction, "_idempotency_replay", False) else 201)


class CorrectionRefundSettlementView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability, RequireRecentReauthentication]
    required_capability = Capability.REFUND_CREATE

    def post(self, request, correction_id):
        try:
            amount_cents = int(request.data.get("amount_cents"))
            correction, refund, result = settle_refund_required_cancellation(
                correction_id=correction_id,
                payment_id=request.data.get("payment_id"),
                amount_cents=amount_cents,
                refund_idempotency_key=request.data.get("refund_idempotency_key", ""),
                cash_point_id=request.data.get("cash_point_id"),
                actor=request.actor_context,
            )
        except (TypeError, ValueError):
            return Response({"code": "INVALID_REFUND", "message": "amount_cents inválido."}, status=400)
        except CorrectionServiceError as error:
            return Response({"code": error.code, "message": error.message}, status=error.status_code)
        return Response(
            {
                "id": str(correction.id),
                "status": correction.status,
                "financial_disposition": correction.financial_disposition,
                "refund_id": str(refund.id),
                "financial_adjustment_id": str(correction.financial_adjustment_id),
                **result,
            },
            status=200 if getattr(correction, "_idempotency_replay", False) else 201,
        )
