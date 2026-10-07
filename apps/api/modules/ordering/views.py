from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.ordering.models import Tab
from modules.ordering.serializers import OrderConfirmSerializer, TabCreateSerializer
from modules.ordering.services import (
    OrderingServiceError,
    confirm_order,
    open_tab,
)


def _error_response(error: OrderingServiceError) -> Response:
    payload = {"code": error.code, "message": error.message}
    if error.details:
        payload.update(error.details)
    return Response(payload, status=error.status_code)


def _tab_payload(tab: Tab) -> dict:
    return {
        "id": str(tab.id),
        "display_label": tab.display_label,
        "state": tab.state,
        "version": tab.version,
        "opened_at": tab.opened_at,
        "closed_at": tab.closed_at,
    }


def _order_payload(order) -> dict:
    items = list(order.items.select_related("product").all())
    return {
        "id": str(order.id),
        "tab_id": str(order.tab_id),
        "source": order.source,
        "status": order.status,
        "confirmed_at": order.confirmed_at,
        "items": [
            {
                "id": str(item.id),
                "product_id": str(item.product_id),
                "product_name": item.product_name_snapshot,
                "unit_price_cents": item.unit_price_cents,
                "quantity": item.quantity,
                "line_total_cents": item.line_total_cents,
                "state": item.state,
            }
            for item in items
        ],
    }


class TabListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tabs = Tab.objects.filter(venue=request.auth.venue).order_by("-opened_at", "id")[:200]
        return Response({"results": [_tab_payload(tab) for tab in tabs]})

    def post(self, request):
        permission = RequireCapability()
        self.required_capability = Capability.TAB_OPEN
        permission.has_permission(request, self)

        serializer = TabCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tab = open_tab(
            actor=request.actor_context,
            **serializer.validated_data,
        )
        return Response(_tab_payload(tab), status=201)


class TabDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, tab_id):
        tab = Tab.objects.filter(pk=tab_id, venue=request.auth.venue).first()
        if not tab:
            return Response(
                {"code": "TAB_NOT_FOUND", "message": "Comanda não encontrada."},
                status=404,
            )
        payload = _tab_payload(tab)
        payload["orders"] = [
            _order_payload(order)
            for order in tab.orders.prefetch_related("items").all()
        ]
        return Response(payload)


class OrderConfirmView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.ORDER_CONFIRM

    def post(self, request, tab_id):
        serializer = OrderConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = confirm_order(
                tab_id=tab_id,
                source="STAFF",
                lines=serializer.validated_data["lines"],
                actor=request.actor_context,
            )
        except OrderingServiceError as error:
            return _error_response(error)
        order = order.__class__.objects.prefetch_related("items").get(pk=order.pk)
        return Response(_order_payload(order), status=201)
