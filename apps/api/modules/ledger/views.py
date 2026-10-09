from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability, RequireRecentReauthentication
from modules.ledger.services import LedgerServiceError, close_tab, collect_payment, create_refund


def error_response(error):
    return Response({"code": error.code, "message": error.message}, status=error.status_code)


class PaymentCollectView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.PAYMENT_COLLECT

    def post(self, request, tab_id):
        class Input(serializers.Serializer):
            amount_cents = serializers.IntegerField(min_value=1, max_value=2147483647)
            method = serializers.CharField(max_length=24)
            idempotency_key = serializers.CharField(max_length=120)
            cash_point_id = serializers.UUIDField(required=False, allow_null=True)
            amount_tendered_cents = serializers.IntegerField(
                min_value=1, max_value=2147483647, required=False, allow_null=True
            )

        data = Input(data=request.data)
        if not data.is_valid():
            return Response(
                {
                    "code": "INVALID_PAYMENT",
                    "message": "Pagamento inválido.",
                    "errors": data.errors,
                },
                status=400,
            )
        try:
            payment, result = collect_payment(
                tab_id=tab_id, actor=request.actor_context, **data.validated_data
            )
        except LedgerServiceError as error:
            return error_response(error)
        return Response(
            {
                "id": str(payment.id),
                "method": payment.method,
                "status": payment.status,
                "confirmed_at": payment.confirmed_at,
                **result,
            },
            status=201,
        )


class PaymentRefundView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability, RequireRecentReauthentication]
    required_capability = Capability.REFUND_CREATE

    def post(self, request, payment_id):
        class Input(serializers.Serializer):
            amount_cents = serializers.IntegerField(min_value=1, max_value=2147483647)
            idempotency_key = serializers.CharField(max_length=120)
            reason = serializers.CharField(max_length=240, required=False, allow_blank=True)
            cash_point_id = serializers.UUIDField(required=False, allow_null=True)

        data = Input(data=request.data)
        if not data.is_valid():
            return Response(
                {"code": "INVALID_REFUND", "message": "Estorno inválido.", "errors": data.errors},
                status=400,
            )
        try:
            refund, result = create_refund(
                payment_id=payment_id, actor=request.actor_context, **data.validated_data
            )
        except LedgerServiceError as error:
            return error_response(error)
        return Response(
            {
                "id": str(refund.id),
                "payment_id": str(refund.payment_id),
                "amount_cents": refund.amount_cents,
                "status": refund.status,
                "confirmed_at": refund.confirmed_at,
                **result,
            },
            status=200 if getattr(refund, "_idempotency_replay", False) else 201,
        )


class TabCloseView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.PAYMENT_COLLECT

    def post(self, request, tab_id):
        try:
            tab = close_tab(tab_id=tab_id, actor=request.actor_context)
        except LedgerServiceError as error:
            return error_response(error)
        return Response(
            {
                "id": str(tab.id),
                "state": tab.state,
                "closed_at": tab.closed_at,
                "version": tab.version,
            }
        )
