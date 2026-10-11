"""Immediate typed emergency guest gate; staff mutations never consult it."""
from django.db import transaction
from django.utils import timezone

from modules.access.capabilities import Capability
from modules.access.models import StaffSession
from modules.access.services import authorize_replayed_command
from modules.audit.services import record_audit_event
from modules.venue.models import Venue
from modules.venue.stations import StationChangeError


def guest_policy_snapshot(venue):
    return {"section": "guest_policy", "blocked": venue.guest_mutations_blocked,
            "version": venue.guest_policy_version}


@transaction.atomic
def set_global_guest_block(*, actor, blocked, expected_version, reason=""):
    venue = Venue.objects.select_for_update(no_key=True).get(pk=actor.venue_id)
    session = StaffSession.objects.select_for_update().filter(pk=actor.session_id).first()
    if session is None:
        raise StationChangeError("AUTH_REQUIRED", "Sessão não encontrada.", 401)
    current_actor = authorize_replayed_command(session_id=actor.session_id,
                                              required_capability=Capability.VENUE_CONFIGURE)
    if actor != current_actor:
        raise StationChangeError("ACTOR_CONTEXT_CHANGED", "Contexto de autorização alterado.", 403)
    before = guest_policy_snapshot(venue)
    if venue.guest_policy_version != expected_version:
        raise StationChangeError("STALE_VERSION", "A política mudou.", details={"current": before})
    venue.guest_mutations_blocked = blocked
    venue.guest_policy_version += 1
    venue.save(update_fields=("guest_mutations_blocked", "guest_policy_version"))
    after = guest_policy_snapshot(venue)
    effective_at = timezone.now().isoformat()
    record_audit_event(actor=actor, event_type="venue.guest_policy_changed", entity_type="Venue",
                      entity_id=str(venue.id), reason=reason,
                      metadata={"before": before, "after": after, "applied_at": effective_at,
                                "effective_at": effective_at, "change_mode": "IMMEDIATE_SAFE"})
    from modules.realtime.services import emit_event
    emit_event(venue_id=venue.id, event_type="venue.configuration_changed", aggregate_type="Venue",
               aggregate_id=venue.id, payload={"section": "guest_policy", "version": venue.guest_policy_version})
    return {**after, "effective_at": effective_at, "change_mode": "IMMEDIATE_SAFE"}
