from django.db.models import Q

from modules.access.models import AccessInvalidationEvent, StaffSession


class AccessInvalidationType:
    SESSION_REVOKED = "SESSION_REVOKED"
    SESSION_SUPERSEDED = "SESSION_SUPERSEDED"
    MEMBERSHIP_CHANGED = "MEMBERSHIP_CHANGED"
    DEVICE_CHANGED = "DEVICE_CHANGED"


def publish_access_invalidation(
    *,
    session: StaffSession | None = None,
    staff_member_id=None,
    device_id=None,
    venue_id=None,
    event_type: str,
    reason: str = "",
    metadata: dict | None = None,
) -> AccessInvalidationEvent:
    resolved_venue_id = venue_id
    if resolved_venue_id is None and session is not None:
        resolved_venue_id = session.venue_id
    if resolved_venue_id is None:
        raise ValueError("venue_id or session is required")

    return AccessInvalidationEvent.objects.create(
        venue_id=resolved_venue_id,
        event_type=event_type,
        staff_member_id=staff_member_id,
        session_id=session.id if session is not None else None,
        device_id=device_id,
        reason=reason,
        metadata=metadata or {},
    )


def relevant_invalidations(
    *,
    session: StaffSession,
    after_id: int = 0,
    limit: int = 100,
):
    audience = Q(session_id=session.id) | Q(staff_member_id=session.staff_member_id)
    if session.device_id:
        audience |= Q(device_id=session.device_id)

    return (
        AccessInvalidationEvent.objects.filter(
            venue_id=session.venue_id,
            id__gt=after_id,
        )
        .filter(audience)
        .order_by("id")[:limit]
    )
