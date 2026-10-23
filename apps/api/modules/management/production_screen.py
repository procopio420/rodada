"""Staff-browser viewport observation of a fresh production station snapshot.

This is a passive *client-reported render*, not an operator acknowledgement, a
human-vision claim, or a domain/order state transition.
"""
import hashlib
import uuid
from datetime import timedelta

from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.management.telemetry import AttendanceTelemetryThrottle
from modules.ordering.models import Order, OrderItem, OrderSource, OrderStatus
from modules.venue.calendar import business_date
from modules.venue.models import (
    AttendanceTelemetryDaily, AttendanceTelemetryReceipt, ProductionScreenReceipt,
)


class ScreenObservationInput(serializers.Serializer):
    station = serializers.ChoiceField(choices=("BAR", "KITCHEN"))
    order_ids = serializers.ListField(
        child=serializers.UUIDField(), allow_empty=False, min_length=1, max_length=20,
    )

    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - {"station", "order_ids"}:
            raise serializers.ValidationError({"non_field_errors": ["Unknown observation fields."]})
        return super().to_internal_value(data)

    def validate_order_ids(self, ids):
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("One observation per Order in the batch.")
        return ids


def _origin_start(venue, order):
    """Use only server ingress of original staff intent, never client wall clocks."""
    if order.source != OrderSource.STAFF or not order.idempotency_key:
        return None
    try:
        key = uuid.UUID(order.idempotency_key)
    except (ValueError, TypeError, AttributeError):
        return None
    # Low-entropy legacy/test command keys are not safe correlation identifiers.
    if key.version != 4:
        return None
    digest = hashlib.sha256(order.idempotency_key.encode("utf-8")).hexdigest()
    return (AttendanceTelemetryReceipt.objects.filter(
        venue=venue, intent_ref=digest, event="intent_started",
    ).order_by("received_at").values_list("received_at", flat=True).first())


class ProductionScreenObservationView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = (AttendanceTelemetryThrottle,)

    def post(self, request):
        if len(request.body) > 8192:
            return Response({"code": "OBSERVATION_TOO_LARGE"}, status=413)
        payload = ScreenObservationInput(data=request.data)
        payload.is_valid(raise_exception=True)
        venue = request.auth.venue
        station = payload.validated_data["station"]
        ids = payload.validated_data["order_ids"]

        orders = list(Order.objects.filter(
            id__in=ids, tab__venue=venue, status=OrderStatus.CONFIRMED,
        ).only("id", "idempotency_key", "source", "confirmed_at"))
        # Reject a mixed batch atomically; do not expose whether a UUID belongs
        # to another tenant or whether an unknown Order exists.
        if len(orders) != len(ids):
            return Response({"code": "SCREEN_ORDER_UNAVAILABLE"}, status=404)
        station_items = set(OrderItem.objects.filter(
            order_id__in=ids,
        ).filter(
            Q(fulfillment_station_snapshot=station) |
            Q(fulfillment_station_snapshot="", product__fulfillment_station=station),
        ).exclude(state__in=("CANCELLED", "DELIVERED")).values_list("order_id", flat=True))
        if station_items != set(ids):
            return Response({"code": "SCREEN_ORDER_UNAVAILABLE"}, status=404)

        observed = 0
        duplicates = 0
        expired = 0
        cutoff = timezone.now() - timedelta(days=7)
        for order in orders:
            # Receipt pruning is 7d: do not re-count an ancient queued order
            # after its first receipt expired. The daily aggregate survives.
            if order.confirmed_at < cutoff:
                expired += 1
                continue
            with transaction.atomic():
                receipt, created = ProductionScreenReceipt.objects.get_or_create(
                    venue=venue, order=order, station=station,
                )
                if not created:
                    duplicates += 1
                    continue
                observed += 1
                start = _origin_start(venue, order)
                latency_ms = None
                if start is not None and start <= receipt.observed_at:
                    latency_ms = int((receipt.observed_at - start).total_seconds() * 1000)
                bucket, _ = AttendanceTelemetryDaily.objects.get_or_create(
                    venue=venue,
                    business_date=business_date(venue, order.confirmed_at),
                    platform="WEB",
                    event="screen_bar" if station == "BAR" else "screen_kitchen",
                )
                AttendanceTelemetryDaily.objects.filter(pk=bucket.pk).update(
                    count=F("count") + 1,
                    duration_total_ms=F("duration_total_ms") + (latency_ms or 0),
                    duration_observed=F("duration_observed") + int(latency_ms is not None),
                )
        return Response(
            {"accepted": True, "first_seen": observed, "duplicate": duplicates, "expired": expired},
            status=202,
        )
