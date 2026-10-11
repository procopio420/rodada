"""Safe typed station commands. Venue lock serializes new routing and changes."""
from dataclasses import dataclass

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from modules.access.capabilities import Capability
from modules.access.services import authorize_replayed_command, recent_reauthentication_valid
from modules.access.models import StaffSession
from modules.audit.services import record_audit_event
from modules.venue.models import StationConfiguration, Venue

STATIONS = ("BAR", "KITCHEN")


@dataclass(frozen=True)
class StationChangeError(Exception):
    code: str
    message: str
    status_code: int = 409
    details: dict | None = None


def station_snapshot(venue_id, station):
    if station not in STATIONS:
        raise StationChangeError("INVALID_STATION", "Estação inválida.", 400)
    row = StationConfiguration.objects.filter(venue_id=venue_id, station=station).first()
    return {"station": station, "enabled": row.enabled if row else True,
            "version": row.version if row else 1, "label": row.label if row else "",
            "updated_at": row.updated_at.isoformat() if row else None}


def station_dependencies(venue_id, station):
    from modules.ordering.models import OrderItem
    from modules.documents_printing.models import PrintJob, StationPrinterBinding

    items = OrderItem.objects.filter(
        Q(fulfillment_station_snapshot=station)
        | Q(fulfillment_station_snapshot="", product__fulfillment_station=station),
        order__tab__venue_id=venue_id, order__status="CONFIRMED",
    ).exclude(state__in=("CANCELLED", "DELIVERED")).order_by("created_at", "id")
    jobs = PrintJob.objects.filter(document__venue_id=venue_id, document__station=station,
                                  document__kind="PRODUCTION_TICKET").exclude(
        state__in=("PRINTED", "OUTPUT_READY", "SPOOL_ACCEPTED", "CANCELLED"))
    return {
        "order_items": [{"id": str(i.id), "order_id": str(i.order_id), "state": i.state}
                        for i in items],
        "print_jobs": [{"id": str(j.id), "state": j.state} for j in jobs.order_by("id")],
        "printer_bindings": [{"endpoint_id": str(b.endpoint_id), "enabled": b.endpoint.enabled}
                            for b in StationPrinterBinding.objects.filter(
                                endpoint__venue_id=venue_id, station=station, enabled=True
                            ).select_related("endpoint").order_by("id")],
    }


def preview_station_change(*, venue_id, station, enabled, label, expected_version):
    current = station_snapshot(venue_id, station)
    dependencies = station_dependencies(venue_id, station)
    blockers = {key: dependencies[key] for key in ("order_items", "print_jobs")
                if not enabled and dependencies[key]}
    return {"current": current, "proposed": {"station": station, "enabled": enabled, "label": label},
            "blockers": blockers, "dependencies": dependencies,
            "can_apply": current["version"] == expected_version and not blockers,
            "change_mode": "REQUIRES_QUIET_STATE" if not enabled else "IMMEDIATE_SAFE",
            "queue_url": "/bar" if station == "BAR" else "/kitchen"}


@transaction.atomic
def apply_station_change(*, actor, station, enabled, label, expected_version, reason=""):
    # Same lock order as confirm_order: Venue -> session -> policy. Never lock items
    # while holding a policy row; transitions may finish independently and safely.
    Venue.objects.select_for_update(no_key=True).get(pk=actor.venue_id)
    session = StaffSession.objects.select_for_update().filter(pk=actor.session_id).first()
    if session is None:
        raise StationChangeError("AUTH_REQUIRED", "Sessão não encontrada.", 401)
    current_actor = authorize_replayed_command(session_id=session.id,
                                              required_capability=Capability.VENUE_CONFIGURE)
    if current_actor != actor:
        raise StationChangeError("ACTOR_CONTEXT_CHANGED", "Contexto de autorização alterado.", 403)
    if not recent_reauthentication_valid(session):
        raise StationChangeError("REAUTH_REQUIRED", "Confirme seu PIN novamente.", 403)
    preview = preview_station_change(venue_id=actor.venue_id, station=station, enabled=enabled,
                                    label=label, expected_version=expected_version)
    if preview["current"]["version"] != expected_version:
        raise StationChangeError("STALE_VERSION", "A configuração mudou.", details=preview)
    if preview["blockers"]:
        raise StationChangeError("STATION_HAS_ACTIVE_WORK", "Resolva o trabalho ativo antes de desativar.", details=preview)
    row, _ = StationConfiguration.objects.get_or_create(venue_id=actor.venue_id, station=station)
    row.enabled, row.label = enabled, label
    row.version += 1
    row.save(update_fields=("enabled", "label", "version", "updated_at"))
    after = station_snapshot(actor.venue_id, station)
    applied_at = timezone.now().isoformat()
    record_audit_event(actor=actor, event_type="venue.configuration_changed",
                      entity_type="StationConfiguration", entity_id=str(row.pk), reason=reason,
                      metadata={"section": "stations", "before": preview["current"], "after": after,
                                "applied_at": applied_at, "effective_at": applied_at,
                                "change_mode": preview["change_mode"]})
    from modules.realtime.services import emit_event
    emit_event(venue_id=actor.venue_id, event_type="venue.configuration_changed",
               aggregate_type="StationConfiguration", aggregate_id=actor.venue_id,
               payload={"section": "stations", "station": station, "version": row.version})
    return {**after, "effective_at": applied_at, "change_mode": preview["change_mode"]}
