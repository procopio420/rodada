from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.ledger.services import LedgerServiceError, close_tab, collect_payment, create_refund


def error_response(error):
    return Response({"code": error.code, "message": error.message}, status=error.status_code)


class PaymentCollectView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.PAYMENT_COLLECT

    def post(self, request, tab_id):
        try:
            amount_cents = int(request.data.get("amount_cents"))
            payment, result = collect_payment(
                tab_id=tab_id,
                amount_cents=amount_cents,
                method=request.data.get("method", ""),
                idempotency_key=request.data.get("idempotency_key", ""),
                cash_point_id=request.data.get("cash_point_id"),
                amount_tendered_cents=(
                    int(request.data["amount_tendered_cents"])
                    if request.data.get("amount_tendered_cents") is not None
                    else None
                ),
                actor=request.actor_context,
            )
        except (TypeError, ValueError):
            return Response({"code": "INVALID_PAYMENT", "message": "amount_cents inválido."}, status=400)
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
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.REFUND_CREATE

    def post(self, request, payment_id):
        try:
            amount_cents = int(request.data.get("amount_cents"))
            refund, result = create_refund(
                payment_id=payment_id,
                amount_cents=amount_cents,
                idempotency_key=request.data.get("idempotency_key", ""),
                reason=request.data.get("reason", ""),
                cash_point_id=request.data.get("cash_point_id"),
                actor=request.actor_context,
            )
        except (TypeError, ValueError):
            return Response({"code": "INVALID_REFUND", "message": "amount_cents inválido."}, status=400)
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
            status=201,
        )


class TabCloseView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.PAYMENT_COLLECT

    def post(self, request, tab_id):
        try:
            tab = close_tab(tab_id=tab_id, actor=request.actor_context)
        except LedgerServiceError as error:
            return error_response(error)
        return Response({"id": str(tab.id), "state": tab.state, "closed_at": tab.closed_at, "version": tab.version})
