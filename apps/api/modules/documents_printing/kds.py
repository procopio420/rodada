"""Authenticated KDS observations; no printing/ordering mutations in this slice."""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from modules.access.capabilities import Capability, has_capability
from modules.access.models import StaffSession
from modules.audit.services import record_audit_event

from .models import KdsDeviceHeartbeat, KdsStationHealth


def station_capability(station):
    if station not in ("BAR", "KITCHEN"):
        raise ValidationError("Estação inválida.")
    return Capability.PRINT_BAR if station == "BAR" else Capability.PRINT_KITCHEN


def active_session(session, station, now):
    return (
        session.is_valid
        and session.device_id is not None
        and session.device.venue_id == session.venue_id
        and session.membership.staff_member_id == session.staff_member_id
        and session.access_expires_at is not None
        and session.access_expires_at > now
        and has_capability(session.membership, station_capability(station))
    )


def locked_health(venue_id, station, now):
    station_capability(station)
    row, _ = KdsStationHealth.objects.get_or_create(
        venue_id=venue_id, station=station,
        defaults={"monitoring_started_at": now, "suspect_since": now},
    )
    return KdsStationHealth.objects.select_for_update().get(pk=row.pk)


def assess_locked(row, now):
    observations = KdsDeviceHeartbeat.objects.filter(
        venue_id=row.venue_id, station=row.station,
        queue_observed_at__isnull=False,
    ).select_related("session__staff_member", "session__membership__staff_member", "session__device")
    accepted = [
        observation.queue_observed_at for observation in observations
        if observation.session.venue_id == row.venue_id
        and observation.session.device_id == observation.device_id
        and active_session(observation.session, row.station, now)
    ]
    latest = max(accepted, default=None)
    if latest is not None and latest <= now:
        row.last_queue_observed_at = max(
            latest, row.last_queue_observed_at or latest,
        )
    ttl = timedelta(seconds=row.heartbeat_ttl_seconds)
    fresh = latest is not None and latest <= now and now - latest < ttl
    if fresh:
        if row.state in ("UNHEALTHY", "RECOVERING"):
            if (
                row.state == "UNHEALTHY" or row.recovery_observed_at is None
                or latest - row.recovery_observed_at >= ttl
            ):
                row.recovery_since = latest
            row.recovery_observed_at = latest
            row.state = "RECOVERING"
            if now - row.recovery_since >= timedelta(seconds=row.recovery_threshold_seconds):
                row.state = "HEALTHY"
                row.recovery_since = row.recovery_observed_at = None
        else:
            row.state = "HEALTHY"
        row.suspect_since = None
    else:
        if row.state == "RECOVERING":
            row.state = "UNHEALTHY"
        elif row.state != "UNHEALTHY":
            # Filtering revoked sessions must not erase a previously accepted
            # expiry boundary. An early revocation/failed read starts absence
            # now; a delayed assessment retains the original missed TTL.
            missing_since = (
                min(now, row.last_queue_observed_at + ttl)
                if row.last_queue_observed_at else row.monitoring_started_at
            )
            row.suspect_since = row.suspect_since or (
                latest + ttl if latest else missing_since
            )
            row.state = "SUSPECT"
            if now - row.suspect_since >= timedelta(seconds=row.failure_threshold_seconds):
                row.state = "UNHEALTHY"
        row.recovery_since = row.recovery_observed_at = None
    row.save()
    return row


@transaction.atomic
def assess_station(*, venue_id, station):
    now = timezone.now()
    return assess_locked(locked_health(venue_id, station, now), now)


@transaction.atomic
def heartbeat(*, session_id, station, queue_observed, client_version=""):
    now = timezone.now()
    session = StaffSession.objects.select_related(
        "staff_member", "membership__staff_member", "device",
    ).get(pk=session_id)
    if not active_session(session, station, now):
        raise PermissionDenied("Session/device not authorized for this station.")
    row = locked_health(session.venue_id, station, now)
    # Assess the previous observation first: a late ping cannot hide a sustained outage.
    assess_locked(row, now)
    observation, _ = KdsDeviceHeartbeat.objects.get_or_create(
        venue_id=session.venue_id, station=station, device_id=session.device_id,
        defaults={"session": session, "seen_at": now},
    )
    # Session rotation cannot inherit an old session's claimed queue observation.
    if observation.session_id != session.id:
        observation.queue_observed_at = None
    observation.session = session
    observation.seen_at = now
    observation.client_version = client_version
    if queue_observed:
        observation.queue_observed_at = now
    else:
        observation.queue_observed_at = None
    observation.save()
    return assess_locked(row, now)


@transaction.atomic
def configure_detector(*, actor, station, expected_version, reason, **thresholds):
    bounds = {
        "heartbeat_ttl_seconds": (5, 300),
        "failure_threshold_seconds": (30, 3600),
        "recovery_threshold_seconds": (30, 3600),
    }
    if set(thresholds) != set(bounds) or any(
        type(value) is not int or not bounds[key][0] <= value <= bounds[key][1]
        for key, value in thresholds.items()
    ):
        raise ValidationError("Limiares tipados inválidos.")
    if not reason.strip():
        raise ValidationError("Motivo obrigatório.")
    session = StaffSession.objects.select_related(
        "staff_member", "membership__staff_member", "device",
    ).get(pk=actor.session_id, venue_id=actor.venue_id)
    if (
        not session.is_valid or session.staff_member_id != actor.staff_id
        or session.membership.staff_member_id != session.staff_member_id
        or session.access_expires_at is None or session.access_expires_at <= timezone.now()
        or not has_capability(session.membership, Capability.PRINT_MANAGE)
    ):
        raise PermissionDenied("Gerência de impressão não autorizada.")
    row = locked_health(actor.venue_id, station, timezone.now())
    if row.version != expected_version:
        from rest_framework.exceptions import APIException

        error = APIException({"code": "KDS_VERSION_CONFLICT", "version": row.version})
        error.status_code = 409
        raise error
    before = {key: getattr(row, key) for key in thresholds}
    for key, value in thresholds.items():
        setattr(row, key, value)
    row.version += 1
    # A new timing policy starts a new observation window; never enables fallback.
    row.state = "SUSPECT"
    row.monitoring_started_at = row.suspect_since = timezone.now()
    row.last_queue_observed_at = None
    row.recovery_since = row.recovery_observed_at = None
    row.save()
    record_audit_event(
        actor=actor, event_type="print.kds_detector_configured",
        entity_type="KdsStationHealth", entity_id=str(row.pk), reason=reason,
        metadata={"station": station, "before": before, "after": thresholds, "version": row.version},
    )
    return row
