from typing import ClassVar

from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.hospitality.tab_display import tab_location_labels
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


def _tab_payload(tab: Tab, *, locations=None) -> dict:
    from modules.house_account.services import financial_position
    if locations is None:
        locations = tab_location_labels([tab.id], include_history=True)
    current, previous = locations
    return {
        "id": str(tab.id),
        "display_label": tab.display_label,
        "table_label": current.get(str(tab.id)),
        "last_table_label": previous.get(str(tab.id)),
        "state": tab.state,
        "version": tab.version,
        "opened_at": tab.opened_at,
        "closed_at": tab.closed_at,
        **financial_position(tab),
    }


def _order_payload(order) -> dict:
    items = list(order.items.select_related("product").prefetch_related("corrections").all())
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
                "quantity": item.quantity if item.state == "CANCELLED" else item.remaining_quantity,
                "original_quantity": item.quantity,
                "remaining_quantity": item.remaining_quantity,
                "line_total_cents": item.line_total_cents if item.state == "CANCELLED" else item.unit_price_cents * item.remaining_quantity,
                "original_line_total_cents": item.line_total_cents,
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
            summary = serializers.BooleanField(default=False)
            q = serializers.CharField(max_length=120, allow_blank=True, default="")
            history_day = serializers.CharField(required=False)
        query = Query(data=request.query_params)
        query.is_valid(raise_exception=True)
        offset = query.validated_data["offset"]
        tabs = Tab.objects.filter(venue=request.auth.venue)
        if query.validated_data["active"]:
            tabs = tabs.filter(state__in=["OPEN", "REQUIRES_ACTION", "SETTLING"])
        history_day = query.validated_data.get("history_day")
        if history_day:
            from datetime import timedelta
            from django.db.models import Q
            from modules.venue.calendar import business_date, business_boundary
            from modules.audit.models import AuditEvent
            if query.validated_data["active"]:
                raise serializers.ValidationError({"history_day": "Histórico não aceita filtro ativo."})
            day = business_date(request.auth.venue) if history_day == "current" else serializers.DateField().run_validation(history_day)
            lower = business_boundary(request.auth.venue, day)
            upper = business_boundary(request.auth.venue, day + timedelta(days=1))
            cancelled = AuditEvent.objects.filter(venue=request.auth.venue, entity_type="Tab",
                event_type="tab.cancelled", occurred_at__gte=lower, occurred_at__lt=upper).values("entity_id")
            # Audit entity IDs are strings; keep the comparison typed on PostgreSQL.
            from django.db.models.functions import Cast
            from django.db.models import CharField
            tabs = tabs.annotate(history_id=Cast("id", CharField())).filter(
                Q(state="CLOSED", closed_at__gte=lower, closed_at__lt=upper) |
                Q(state="CANCELLED", history_id__in=cancelled))
            history_day = day.isoformat()
        from .search import normalize_tab_label

        label_query = normalize_tab_label(query.validated_data["q"])
        if label_query:
            tabs = tabs.filter(search_label__contains=label_query)
        rows = list(tabs.order_by("-opened_at", "id")[offset:offset + 201])
        locations = tab_location_labels([tab.id for tab in rows[:200]], include_history=True)
        if query.validated_data["summary"]:
            # Attendance needs identity and placement only. Avoid N+1 financial
            # position queries for every open tab on a busy venue's live list.
            current, previous = locations
            results = [
                {
                    "id": str(tab.id),
                    "display_label": tab.display_label,
                    "table_label": current.get(str(tab.id)),
                    "last_table_label": previous.get(str(tab.id)),
                    "state": tab.state,
                    "opened_at": tab.opened_at,
                }
                for tab in rows[:200]
            ]
        else:
            results = [_tab_payload(tab, locations=locations) for tab in rows[:200]]
        return Response({"results": results,
                         **({"history_business_date": history_day} if history_day else {}),
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

    @transaction.atomic
    def get(self, request, tab_id):
        tab = Tab.objects.select_for_update().filter(pk=tab_id, venue=request.auth.venue).first()
        if not tab:
            return Response(
                {"code": "TAB_NOT_FOUND", "message": "Comanda não encontrada."},
                status=404,
            )
        from rest_framework import serializers

        class ContextQuery(serializers.Serializer):
            occupancy_id = serializers.UUIDField(required=False)
            table_id = serializers.UUIDField(required=False)

        context_query = ContextQuery(data=request.query_params)
        context_query.is_valid(raise_exception=True)
        context = context_query.validated_data
        if bool(context.get("occupancy_id")) != bool(context.get("table_id")):
            return Response({"code": "INVALID_TABLE_CONTEXT", "message": "Informe mesa e ocupação juntas."}, status=400)
        if context:
            from django.db.models import F

            from modules.hospitality.models import TabOccupancyAssignment

            valid = TabOccupancyAssignment.objects.filter(
                tab=tab, occupancy_id=context["occupancy_id"], occupancy__table_id=context["table_id"],
                released_at__isnull=True, occupancy__released_at__isnull=True,
                occupancy__table__venue=request.auth.venue, occupancy__table__status="OCCUPIED",
                occupancy__generation=F("occupancy__table__access_generation"),
            ).exists()
            if not valid:
                return Response({"code": "TABLE_CONTEXT_CHANGED", "message": "O vínculo da comanda com a mesa mudou. Atualize as mesas."}, status=409)
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
                "financial_disposition": correction.financial_disposition,
                "refund_required_cents": correction.refund_required_cents,
            }
            for correction in OrderCorrection.objects.filter(
                original_order_item__order__tab=tab,
                status="REQUESTED",
                financial_disposition__in=("REFUND_REQUIRED", "MANUAL_REVIEW_REQUIRED"),
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


class ProductionBatchView(APIView):
    permission_classes: ClassVar[list] = [IsAuthenticated, RequireCapability]
    required_capability = Capability.ORDER_CONFIRM

    def post(self, request):
        from .production import execute_production_batch
        from .serializers import ProductionBatchSerializer

        serializer = ProductionBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            receipt = execute_production_batch(actor=request.actor_context, **serializer.validated_data)
        except OrderingServiceError as error:
            return _error_response(error)
        return Response(receipt, status=409 if receipt["status"] == "REJECTED" else 200)


class ProductionQueueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, station):
        from .production import snapshot_fingerprint
        if station not in ("BAR", "KITCHEN"):
            return Response({"code": "INVALID_STATION", "message": "Estação inválida."}, status=400)
        from django.db.models import Q
        rows = OrderItem.objects.filter(Q(fulfillment_station_snapshot=station) | Q(fulfillment_station_snapshot="", product__fulfillment_station=station), order__tab__venue=request.auth.venue, order__status="CONFIRMED").exclude(state__in=["CANCELLED", "DELIVERED"]).select_related("order__tab", "product").prefetch_related("corrections").order_by("created_at")
        rows = list(rows)
        current, _ = tab_location_labels({item.order.tab_id for item in rows})
        return Response({"results": [{"id": str(item.id), "product_id": str(item.product_id), "order_id": str(item.order_id), "tab_id": str(item.order.tab_id), "state": item.state, "quantity": item.remaining_quantity, "product_name": item.product_name_snapshot, "customization_snapshot": item.customization_snapshot, "snapshot_fingerprint": snapshot_fingerprint(item.customization_snapshot), "tab_label": item.order.tab.display_label, "table_label": current.get(str(item.order.tab_id)), "created_at": item.created_at, "ready_at": item.ready_at} for item in rows]})
