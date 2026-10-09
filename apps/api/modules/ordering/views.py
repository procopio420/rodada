from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.ordering.models import OrderItem, Tab
from modules.ordering.serializers import OrderConfirmSerializer, TabCreateSerializer
from modules.ordering.services import (
    OrderingServiceError,
    confirm_order,
    open_tab,
    transition_order_item,
)


def _error_response(error: OrderingServiceError) -> Response:
    payload = {"code": error.code, "message": error.message}
    if error.details:
        payload.update(error.details)
    return Response(payload, status=error.status_code)


def _tab_payload(tab: Tab) -> dict:
    from modules.house_account.services import financial_position
    return {
        "id": str(tab.id),
        "display_label": tab.display_label,
        "state": tab.state,
        "version": tab.version,
        "opened_at": tab.opened_at,
        "closed_at": tab.closed_at,
        **financial_position(tab),
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
                "customization_snapshot": item.customization_snapshot,
                "unit_price_cents": item.unit_price_cents,
                "quantity": item.quantity,
                "line_total_cents": item.line_total_cents,
                "state": item.state,
                "accepted_at": item.accepted_at,
                "ready_at": item.ready_at,
                "delivered_at": item.delivered_at,
            }
            for item in items
        ],
    }


class TabListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from rest_framework import serializers
        class Query(serializers.Serializer):
            offset = serializers.IntegerField(min_value=0, default=0)
            active = serializers.BooleanField(default=False)
        query = Query(data=request.query_params)
        query.is_valid(raise_exception=True)
        offset = query.validated_data["offset"]
        tabs = Tab.objects.filter(venue=request.auth.venue)
        if query.validated_data["active"]:
            tabs = tabs.filter(state__in=["OPEN", "REQUIRES_ACTION", "SETTLING"])
        rows = list(tabs.order_by("-opened_at", "id")[offset:offset + 201])
        return Response({"results": [_tab_payload(tab) for tab in rows[:200]],
                         "next_offset": offset + 200 if len(rows) > 200 else None})

    def post(self, request):
        permission = RequireCapability()
        self.required_capability = Capability.TAB_OPEN
        permission.has_permission(request, self)

        serializer = TabCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tab = open_tab(actor=request.actor_context, **serializer.validated_data)
        except OrderingServiceError as error:
            return _error_response(error)
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
        from modules.corrections.models import OrderCorrection
        from modules.ledger.models import RefundStatus

        payments = tab.payments.prefetch_related("refunds").order_by("received_at", "id")
        payload["payments"] = [
            {
                "id": str(payment.id),
                "amount_cents": payment.amount_cents,
                "method": payment.method,
                "status": payment.status,
                "confirmed_at": payment.confirmed_at,
                "simulated": payment.provider.startswith("simulator:"),
                "refunded_cents": sum(
                    refund.amount_cents
                    for refund in payment.refunds.all()
                    if refund.status == RefundStatus.CONFIRMED
                ),
                "refunds": [
                    {
                        "id": str(refund.id),
                        "amount_cents": refund.amount_cents,
                        "status": refund.status,
                        "reason": refund.reason,
                        "confirmed_at": refund.confirmed_at,
                    }
                    for refund in payment.refunds.all()
                ],
            }
            for payment in payments
        ]
        payload["refund_required_corrections"] = [
            {
                "id": str(correction.id),
                "order_item_id": str(correction.original_order_item_id),
                "item_name": correction.original_order_item.product_name_snapshot,
                "reason_code": correction.reason_code,
                "refund_required_cents": correction.refund_required_cents,
            }
            for correction in OrderCorrection.objects.filter(
                original_order_item__order__tab=tab,
                status="REQUESTED",
                financial_disposition="REFUND_REQUIRED",
            ).select_related("original_order_item")
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
                idempotency_key=serializer.validated_data["idempotency_key"],
                actor=request.actor_context,
            )
        except OrderingServiceError as error:
            return _error_response(error)
        replayed = getattr(order, "_idempotency_replay", False)
        order = order.__class__.objects.prefetch_related("items").get(pk=order.pk)
        return Response(
            _order_payload(order),
            status=200 if replayed else 201,
        )


class OrderItemTransitionView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.ORDER_CONFIRM

    def post(self, request, item_id):
        try:
            item = transition_order_item(item_id=item_id, target_state=request.data.get("state", ""), actor=request.actor_context)
        except OrderingServiceError as error:
            return _error_response(error)
        return Response({"id": str(item.id), "state": item.state, "ready_at": item.ready_at})


class ProductionQueueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, station):
        if station not in ("BAR", "KITCHEN"):
            return Response({"code": "INVALID_STATION", "message": "Estação inválida."}, status=400)
        from django.db.models import Q
        rows = OrderItem.objects.filter(Q(fulfillment_station_snapshot=station) | Q(fulfillment_station_snapshot="", product__fulfillment_station=station), order__tab__venue=request.auth.venue, order__status="CONFIRMED").exclude(state__in=["CANCELLED", "DELIVERED"]).select_related("order__tab", "product").order_by("created_at")
        return Response({"results": [{"id": str(item.id), "product_id": str(item.product_id), "order_id": str(item.order_id), "tab_id": str(item.order.tab_id), "state": item.state, "quantity": item.quantity, "product_name": item.product_name_snapshot, "customization_snapshot": item.customization_snapshot, "tab_label": item.order.tab.display_label, "created_at": item.created_at, "ready_at": item.ready_at} for item in rows]})
