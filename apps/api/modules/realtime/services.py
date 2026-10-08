"""Public publication port. Invoke inside the domain mutation transaction."""

from datetime import timedelta

from django.db import connection, transaction
from django.utils import timezone

from .models import OutboxEvent, VenueStream

RETENTION = timedelta(hours=24)


def emit_event(*, venue_id, event_type, aggregate_type, aggregate_id, tab_id=None, payload=None):
    if not connection.in_atomic_block:
        raise RuntimeError("emit_event requires the domain mutation transaction")
    VenueStream.objects.get_or_create(venue_id=venue_id)
    stream = VenueStream.objects.select_for_update().get(venue_id=venue_id)
    stream.sequence += 1
    stream.save(update_fields=["sequence"])
    return OutboxEvent.objects.create(
        venue_id=venue_id,
        sequence=stream.sequence,
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=str(aggregate_id),
        tab_id=tab_id,
        payload=payload or {},
    )


def snapshot_cursor(venue_id):
    sequence = (
        VenueStream.objects.filter(venue_id=venue_id).values_list("sequence", flat=True).first()
        or 0
    )
    return f"{venue_id}:{sequence}"


def dispatch_pending(limit=100):
    """Persist publication before SSE delivery. Concurrent workers serialize per venue.

    A crash before commit retries the batch; a crash after commit leaves it replayable.
    Redis is deliberately optional and no network operation runs in this transaction.
    """
    total = 0
    venues = list(
        OutboxEvent.objects.filter(published_at__isnull=True)
        .values_list("venue_id", flat=True)
        .distinct()[:limit]
    )
    for venue_id in venues:
        with transaction.atomic():
            VenueStream.objects.select_for_update().get(venue_id=venue_id)
            ids = list(
                OutboxEvent.objects.filter(venue_id=venue_id, published_at__isnull=True)
                .order_by("sequence")
                .values_list("id", flat=True)[: limit - total]
            )
            total += OutboxEvent.objects.filter(id__in=ids).update(published_at=timezone.now())
        if total >= limit:
            break
    return total


def parse_cursor(venue_id, cursor):
    try:
        prefix, value = cursor.rsplit(":", 1)
        sequence = int(value)
        if prefix != str(venue_id) or sequence < 0:
            return None
        return sequence
    except (ValueError, AttributeError):
        return None


def replay_batch(venue_id, cursor, limit=100):
    sequence = parse_cursor(venue_id, cursor)
    current = parse_cursor(venue_id, snapshot_cursor(venue_id))
    if sequence is None or sequence > current:
        return None
    # Even the supplied baseline must be retained unless it is the current head.
    if (
        sequence
        and sequence != current
        and not OutboxEvent.objects.filter(
            venue_id=venue_id, sequence=sequence, occurred_at__gte=timezone.now() - RETENTION
        ).exists()
    ):
        return None
    rows = list(
        OutboxEvent.objects.filter(venue_id=venue_id, sequence__gt=sequence).order_by("sequence")[
            :limit
        ]
    )
    expected = sequence + 1
    published = []
    for row in rows:
        if row.sequence != expected or row.occurred_at < timezone.now() - RETENTION:
            return None
        if row.published_at is None:
            break
        published.append(row)
        expected += 1
    if not rows and sequence < current:
        return None
    return published
