from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.ledger.models import PaymentMethod
from modules.ledger.services import LedgerServiceError, close_tab, collect_payment


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
                actor=request.actor_context,
            )
        except (TypeError, ValueError):
            return Response({"code": "INVALID_PAYMENT", "message": "amount_cents inválido."}, status=400)
        except LedgerServiceError as error:
            return error_response(error)
        return Response({"id": str(payment.id), "method": payment.method, **result}, status=201)


class TabCloseView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.PAYMENT_COLLECT

    def post(self, request, tab_id):
        try:
            tab = close_tab(tab_id=tab_id, actor=request.actor_context)
        except LedgerServiceError as error:
            return error_response(error)
        return Response({"id": str(tab.id), "state": tab.state, "closed_at": tab.closed_at, "version": tab.version})
