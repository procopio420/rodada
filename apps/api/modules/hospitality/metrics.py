"""Read-only Spec 004 TABLE-005 metrics from canonical operational timestamps.

The release business date owns a visit's durations, even when cleaning finishes
later. Starts and ready events are separately counted in their own business day.
No inferred states, artificial zero durations, or financial joins.
"""

from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from modules.hospitality.models import Table, TableOccupancy
from modules.ordering.models import Order, OrderSource, OrderStatus
from modules.venue.calendar import business_boundary, business_date

TIMINGS = {
    "occupancy": ("started_at", "released_at"),
    "wait_to_clean": ("released_at", "cleaning_started_at"),
    "cleaning": ("cleaning_started_at", "ready_at"),
    "release_to_ready": ("released_at", "ready_at"),
}


def _empty():
    return {
        "started": 0,
        "released": 0,
        "ready": 0,
        "timings": {
            key: {"eligible": 0, "observed": 0, "missing": 0, "invalid": 0,
                  "mean_seconds": None, "_total": 0.0}
            for key in TIMINGS
        },
        "orders": {"guest": 0, "staff": 0, "cancelled": 0, "unknown_source": 0,
                   "denominator": 0, "guest_percent": None},
    }


def _record(bucket, occupancy):
    for key, (from_field, to_field) in TIMINGS.items():
        metric = bucket["timings"][key]
        metric["eligible"] += 1
        earlier, later = getattr(occupancy, from_field), getattr(occupancy, to_field)
        if earlier is None or later is None:
            metric["missing"] += 1
        elif later < earlier or (
            key in ("wait_to_clean", "cleaning", "release_to_ready")
            and occupancy.cleaning_started_at is not None
            and (
                occupancy.cleaning_started_at < occupancy.released_at
                or (
                    occupancy.ready_at is not None
                    and occupancy.ready_at < occupancy.cleaning_started_at
                )
            )
        ):
            metric["invalid"] += 1
        else:
            metric["_total"] += (later - earlier).total_seconds()
            metric["observed"] += 1


def _finish(bucket):
    for metric in bucket["timings"].values():
        total = metric.pop("_total")
        if metric["observed"]:
            metric["mean_seconds"] = round(total / metric["observed"])
    orders = bucket["orders"]
    orders["denominator"] = orders["guest"] + orders["staff"]
    if orders["denominator"]:
        orders["guest_percent"] = round(100 * orders["guest"] / orders["denominator"], 1)
    return bucket


def table_turnover_report(*, venue, start, end):
    """Return distinct, Venue-scoped counts and observed durations.

    No 'turns per hour': the canonical model does not store historical table
    availability exposure. Current inventory is only a label/denominator context.
    """
    lower = business_boundary(venue, start)
    upper = business_boundary(venue, end + timedelta(days=1))
    dates = [start + timedelta(days=n) for n in range((end - start).days + 1)]
    daily = {day: _empty() for day in dates}
    table_rows = {
        str(table.id): {"table_id": str(table.id), "label": table.label, **_empty()}
        for table in Table.objects.filter(venue=venue).only("id", "label")
    }
    summary = _empty()

    def day_for(instant):
        return business_date(venue, instant)

    occupancies = (
        TableOccupancy.objects.filter(table__venue=venue)
        .filter(
            Q(started_at__gte=lower, started_at__lt=upper)
            | Q(released_at__gte=lower, released_at__lt=upper)
            | Q(ready_at__gte=lower, ready_at__lt=upper)
        )
        .select_related("table")
    )
    for occupancy in occupancies.iterator():
        row = table_rows[str(occupancy.table_id)]
        for field, count_key in (
            ("started_at", "started"),
            ("released_at", "released"),
            ("ready_at", "ready"),
        ):
            instant = getattr(occupancy, field)
            if instant is not None and (day := day_for(instant)) in daily:
                for bucket in (summary, daily[day], row):
                    bucket[count_key] += 1
        if occupancy.released_at is not None and (day := day_for(occupancy.released_at)) in daily:
            for bucket in (summary, daily[day], row):
                _record(bucket, occupancy)

    orders = (
        Order.objects.filter(
            tab__venue=venue, confirmed_at__gte=lower, confirmed_at__lt=upper
        )
        .values_list("confirmed_at", "source", "status")
    )
    for confirmed_at, source, status in orders.iterator():
        bucket = daily.get(day_for(confirmed_at))
        if bucket is None:
            continue
        if status != OrderStatus.CONFIRMED:
            key = "cancelled"
        elif source == OrderSource.GUEST:
            key = "guest"
        elif source in (OrderSource.STAFF, OrderSource.CASHIER):
            key = "staff"
        else:
            key = "unknown_source"
        for target in (summary, bucket):
            target["orders"][key] += 1

    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "timezone": venue.timezone,
        "cutoff_hour": venue.business_day_cutoff_hour,
        "generated_at": timezone.now().isoformat(),
        "definitions": {
            "turnover": "Contagem de ocupações liberadas, pelo dia operacional de released_at; não representa giro por hora nem capacidade.",
            "durations": "Médias em segundos de eventos observados válidos, atribuídas ao dia operacional de released_at; limpeza concluída depois do fim do período pode compor a média.",
            "missing": "eligible é número de liberações; missing é ausência de timestamp; invalid é cronologia inconsistente. Sem amostras, média null.",
            "orders": "Pedidos cujo estado atual é CONFIRMED, pelo confirmed_at; staff inclui CASHIER; cancelados e origens desconhecidas ficam fora do denominador Guest/Staff.",
            "inventory": "Rótulos de mesa atuais. Não há exposição histórica de mesas disponíveis para calcular giro por hora.",
        },
        "summary": _finish(summary),
        "daily": [{"date": day.isoformat(), **_finish(bucket)} for day, bucket in daily.items()],
        "tables": sorted(
            (_finish(row) for row in table_rows.values()),
            key=lambda row: (row["label"].casefold(), row["table_id"]),
        ),
    }
