"""Management-only metadata CAS. This never activates delivery in S1."""

from django.core.exceptions import ValidationError
from django.db import transaction

from modules.access.agent_credentials import authorize_manager
from modules.access.context import ActorContext
from modules.access.models import StaffSession
from modules.audit.services import record_audit_event

from .models import AgentPrinterRoute


@transaction.atomic
def configure_route(
    *,
    route_id,
    session: StaffSession,
    expected_version: int,
    priority: int,
    profile_id: str,
    destination: str,
    port: int,
) -> AgentPrinterRoute:
    route = (
        AgentPrinterRoute.objects.select_for_update(of=("self",))
        .select_related("endpoint", "printer__agent__device")
        .get(pk=route_id, endpoint__venue_id=session.venue_id)
    )
    authorize_manager(session, route.printer.agent)
    if route.version != expected_version:
        raise ValidationError("Route configuration version conflict.")
    before = {key: getattr(route, key) for key in ("priority", "profile_id", "destination", "port")}
    route.priority = priority
    route.profile_id = profile_id
    route.destination = destination
    route.port = port
    route.version += 1
    route.full_clean()
    route.save(
        update_fields=["priority", "profile_id", "destination", "port", "version", "updated_at"]
    )
    record_audit_event(
        actor=ActorContext.from_session(session),
        event_type="print.agent_route_configured",
        entity_type="AgentPrinterRoute",
        entity_id=str(route.id),
        metadata={
            "before": before,
            "after": {key: getattr(route, key) for key in before},
            "version": route.version,
        },
    )
    return route
