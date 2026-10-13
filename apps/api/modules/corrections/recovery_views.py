"""Read-only, capability-scoped resolution of the immutable recovery target."""
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.corrections.models import OrderCorrection
from modules.ledger.models import Payment
from modules.ordering.models import OrderItem


def _missing():
    return Response({"code": "RECOVERY_CONTEXT_NOT_FOUND", "message": "Contexto original não encontrado."}, status=404)


class OrderItemRecoveryContextView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.ORDER_CORRECT

    def get(self, request, item_id):
        item = OrderItem.objects.filter(pk=item_id, order__tab__venue=request.auth.venue).select_related("order").first()
        if item is None:
            return _missing()
        return Response({"tab_id": str(item.order.tab_id), "order_item_id": str(item.id)})


class PaymentRecoveryContextView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.REFUND_CREATE

    def get(self, request, payment_id):
        payment = Payment.objects.filter(pk=payment_id, tab__venue=request.auth.venue).first()
        if payment is None:
            return _missing()
        return Response({"tab_id": str(payment.tab_id), "payment_id": str(payment.id)})


class CorrectionRecoveryContextView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.REFUND_CREATE

    def get(self, request, correction_id):
        class Query(serializers.Serializer):
            payment_id = serializers.UUIDField()

        query = Query(data=request.query_params)
        query.is_valid(raise_exception=True)
        correction = OrderCorrection.objects.filter(
            pk=correction_id, venue=request.auth.venue,
            original_order_item__order__tab__venue=request.auth.venue,
        ).select_related("original_order_item__order").first()
        if correction is None:
            return _missing()
        tab_id = correction.original_order_item.order.tab_id
        payment = Payment.objects.filter(pk=query.validated_data["payment_id"], tab_id=tab_id, tab__venue=request.auth.venue).first()
        if payment is None:
            return _missing()
        return Response({"tab_id": str(tab_id), "order_item_id": str(correction.original_order_item_id),
                         "payment_id": str(payment.id), "correction_id": str(correction.id),
                         "correction_status": correction.status})
