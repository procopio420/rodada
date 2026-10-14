from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability, RequireRecentReauthentication
from modules.corrections.models import CorrectionKind
from modules.corrections.services import (
    CorrectionServiceError,
    cancel_before_fulfillment,
    create_post_production_correction,
    settle_cancellation_without_refund,
    settle_refund_required_cancellation,
)
from modules.ledger.services import LedgerServiceError, reverse_open_responsibility, totals
from modules.ordering.models import OrderItem


class OrderItemCancelView(APIView):
    """The only staff mutation which can cancel a confirmed order item."""

    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.ORDER_CORRECT

    def post(self, request, item_id):
        if "quantity" in request.data and request.data["quantity"] is None:
            return Response({"code": "INVALID_CANCELLATION_QUANTITY", "message": "Quantidade inválida."}, status=400)
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
                quantity=request.data.get("quantity"),
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
            "refund_required_cents": correction.refund_required_cents,
            "order_item_id": str(item.id),
            "order_item_state": item.state,
            "quantity_cancelled": correction.quantity_cancelled,
            "remaining_quantity": item.remaining_quantity,
            **totals(item.order.tab),
        }
        if correction.status == "REQUESTED":
            return Response(payload, status=200 if getattr(correction, "_idempotency_replay", False) else 202)
        return Response(payload, status=200 if getattr(correction, "_idempotency_replay", False) else 201)


class CorrectionWithoutRefundSettlementView(APIView):
    permission_classes = (IsAuthenticated, RequireCapability, RequireRecentReauthentication)
    required_capability = Capability.ORDER_CORRECT

    def post(self, request, correction_id):
        if request.data:
            return Response({"code": "INVALID_REVIEW", "message": "A revisão usa somente a correção original."}, status=400)
        try:
            correction, result = settle_cancellation_without_refund(
                correction_id=correction_id, actor=request.actor_context,
            )
        except CorrectionServiceError as error:
            return Response({"code": error.code, "message": error.message}, status=error.status_code)
        return Response({"id": str(correction.id), "status": correction.status,
                         "financial_disposition": correction.financial_disposition,
                         "financial_adjustment_id": str(correction.financial_adjustment_id) if correction.financial_adjustment_id else None,
                         "refund_id": None, **result},
                        status=200 if getattr(correction, "_idempotency_replay", False) else 201)


class CorrectionRefundSettlementView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability, RequireRecentReauthentication]
    required_capability = Capability.REFUND_CREATE

    def post(self, request, correction_id):
        class Input(serializers.Serializer):
            payment_id = serializers.UUIDField()
            amount_cents = serializers.IntegerField(min_value=1, max_value=2147483647)
            refund_idempotency_key = serializers.CharField(max_length=120)
            cash_point_id = serializers.UUIDField(required=False, allow_null=True)
            originating_session_id = serializers.UUIDField(required=False)

        data = Input(data=request.data)
        if not data.is_valid():
            return Response({"code": "INVALID_REFUND", "message": "Estorno inválido.", "errors": data.errors}, status=400)
        try:
            correction, refund, result = settle_refund_required_cancellation(
                correction_id=correction_id,
                amount_cents=data.validated_data["amount_cents"],
                payment_id=data.validated_data["payment_id"],
                refund_idempotency_key=data.validated_data["refund_idempotency_key"],
                cash_point_id=data.validated_data.get("cash_point_id"),
                originating_session_id=data.validated_data.get("originating_session_id"),
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
                "refund_status": refund.status,
                "financial_adjustment_id": str(correction.financial_adjustment_id),
                **result,
            },
            status=200 if getattr(correction, "_idempotency_replay", False) else 201,
        )


class PostProductionCorrectionView(APIView):
    """Manager command for a real remake/replacement after work has started."""

    permission_classes = [IsAuthenticated, RequireCapability, RequireRecentReauthentication]
    required_capability = Capability.ORDER_CORRECT

    def post(self, request, item_id):
        try:
            correction = create_post_production_correction(
                item_id=item_id,
                kind=request.data.get("kind", ""),
                reason_code=request.data.get("reason_code", ""),
                reason_text=request.data.get("reason_text", ""),
                idempotency_key=request.data.get("idempotency_key", ""),
                replacement_product_id=request.data.get("replacement_product_id"),
                actor=request.actor_context,
            )
        except CorrectionServiceError as error:
            payload = {"code": error.code, "message": error.message}
            if error.details:
                payload.update(error.details)
            return Response(payload, status=error.status_code)
        item = OrderItem.objects.select_related("order__tab").get(pk=item_id)
        replacement = correction.replacement_order_item
        original_total_cents = item.line_total_cents
        replacement_total_cents = replacement.line_total_cents if replacement is not None else None
        return Response(
            {
                "id": str(correction.id),
                "status": correction.status,
                "kind": correction.kind,
                "financial_disposition": correction.financial_disposition,
                "financial_adjustment_id": (
                    str(correction.financial_adjustment_id) if correction.financial_adjustment_id else None
                ),
                "replacement_order_item_id": (
                    str(correction.replacement_order_item_id)
                    if correction.replacement_order_item_id
                    else None
                ),
                "refund_required_cents": correction.refund_required_cents,
                "order_item_id": str(item.id),
                "order_item_state": item.state,
                # Financial presentation stays server-authoritative.  The native
                # client must not infer a replacement delta from its stale catalog.
                "original_line_total_cents": original_total_cents,
                "replacement_line_total_cents": replacement_total_cents,
                "financial_delta_cents": (
                    replacement_total_cents - original_total_cents
                    if replacement_total_cents is not None
                    else -original_total_cents
                ),
                **totals(item.order.tab),
            },
            status=200 if getattr(correction, "_idempotency_replay", False) else 201,
        )
