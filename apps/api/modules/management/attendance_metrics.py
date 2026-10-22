"""Aggregate canonical observations, never infer client intent or delivery."""
from datetime import timedelta
from django.db.models import Sum

from modules.dispatch.models import DispatchTask, DispatchTaskType
from modules.ordering.models import OrderItem, OrderStatus
from modules.venue.calendar import business_boundary
from modules.venue.models import AttendanceTelemetryDaily


def _bucket(source):
    return {"source": source, "eligible": 0, "observed": 0, "missing": 0,
            "invalid": 0, "unverified": 0, "mean_seconds": None, "_seconds": 0.0}


def _observe(bucket, start, end, *, verified=True):
    bucket["eligible"] += 1
    if not verified:
        bucket["unverified"] += 1
    elif start is None or end is None:
        bucket["missing"] += 1
    elif end < start:
        bucket["invalid"] += 1
    else:
        bucket["observed"] += 1
        bucket["_seconds"] += (end - start).total_seconds()


def attendance_metrics(*, venue, start, end):
    lower = business_boundary(venue, start)
    upper = business_boundary(venue, end + timedelta(days=1))
    production = {station: {
        "confirmed_to_accepted": _bucket("Order.confirmed_at→OrderItem.accepted_at"),
        "confirmed_to_ready": _bucket("Order.confirmed_at→OrderItem.ready_at"),
    } for station in ("BAR", "KITCHEN", "UNKNOWN")}
    calls = {kind: {
        "created_to_claimed": _bucket("DispatchTask.created_at→claimed_at"),
        "created_to_completed": _bucket("DispatchTask.created_at→completed_at"),
    } for kind in (DispatchTaskType.SERVICE_REQUEST, DispatchTaskType.BILL_REQUEST)}
    delivery = _bucket("DispatchTask.ready_at→completed_at; completion_source=MANUAL")
    bill_close = _bucket("DispatchTask.created_at→requested_tab.closed_at")

    # Iterator + values_list: bounded memory and no relation-fetch per row.
    items = OrderItem.objects.filter(order__tab__venue=venue,
        order__status=OrderStatus.CONFIRMED,
        order__confirmed_at__gte=lower, order__confirmed_at__lt=upper).values_list(
            "fulfillment_station_snapshot", "order__confirmed_at", "accepted_at", "ready_at")
    for station, confirmed, accepted, ready in items.iterator():
        bucket = production[station if station in ("BAR", "KITCHEN") else "UNKNOWN"]
        _observe(bucket["confirmed_to_accepted"], confirmed, accepted)
        _observe(bucket["confirmed_to_ready"], confirmed, ready)

    tasks = DispatchTask.objects.filter(venue=venue, created_at__gte=lower,
        created_at__lt=upper, task_type__in=[*calls, DispatchTaskType.DELIVERY]).values_list(
            "task_type", "created_at", "claimed_at", "completed_at", "ready_at",
            "completion_source", "requested_tab__venue_id", "requested_tab__closed_at")
    for kind, created, claimed, completed, ready, source, tab_venue, closed in tasks.iterator():
        if kind in calls:
            _observe(calls[kind]["created_to_claimed"], created, claimed)
            _observe(calls[kind]["created_to_completed"], created, completed)
            if kind == DispatchTaskType.BILL_REQUEST:
                _observe(bill_close, created, closed if tab_venue == venue.pk else None)
        else:
            _observe(delivery, ready, completed, verified=source == "MANUAL")

    buckets = [delivery, bill_close]
    for group in [*production.values(), *calls.values()]:
        buckets.extend(group.values())
    for bucket in buckets:
        total = bucket.pop("_seconds")
        if bucket["observed"]:
            bucket["mean_seconds"] = round(total / bucket["observed"], 3)
    client_telemetry = list(AttendanceTelemetryDaily.objects.filter(venue=venue, business_date__gte=start, business_date__lte=end).values("platform", "event").annotate(count_total=Sum("count"), duration_total_ms=__import__("django").db.models.Sum("duration_total_ms"), duration_observed=__import__("django").db.models.Sum("duration_observed")).order_by("platform", "event"))
    return {"client_telemetry": client_telemetry, "start": start, "end": end, "timezone": venue.timezone,
        "cutoff_hour": venue.business_day_cutoff_hour,
        "cohort": "Order.confirmed_at / DispatchTask.created_at; final timestamps may follow period",
        "production": production, "calls": calls, "manual_delivery": delivery,
        "bill_to_tab_closed": bill_close,
        "not_instrumented": ["client_steps", "client_intent_started", "client_attempts",
                             "client_errors", "presentation_version", "production_screen_received"]}
