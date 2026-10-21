"""Multiagent delivery on the existing fenced PrintJob lifecycle (S3)."""

import base64
import hashlib
from datetime import timedelta

from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, ValidationError

from modules.access.agent_credentials import validate_agent
from modules.access.context import ActorContext
from modules.access.models import AgentCredential
from modules.audit.services import record_audit_event

from .models import (
    AgentPrinterRoute,
    DiscoveredPrinter,
    PrintAgent,
    PrintAttempt,
    PrinterEndpoint,
    PrintJob,
)
from .profiles import PROFILES, render_profile, supports
from .services import claim_job, finish_attempt, recover_expired


def locked_identity(agent, credential_id):
    agent = (
        PrintAgent.objects.select_for_update(of=("self",))
        .select_related("venue", "device")
        .get(pk=agent.pk)
    )
    validate_agent(agent)
    if not AgentCredential.objects.filter(
        pk=credential_id, agent=agent, revoked_at__isnull=True, expires_at__gt=timezone.now()
    ).exists():
        raise AuthenticationFailed("Credential expired or revoked.")
    return agent


def delivery_enabled(agent):
    return (
        agent.version in ("0.3.0", "0.5.0")
        and AgentPrinterRoute.objects.filter(
            printer__agent=agent, endpoint__adapter="AGENT", endpoint__enabled=True, enabled=True
        ).exists()
    )


@transaction.atomic
def discover(agent, credential_id, printers):
    agent = locked_identity(agent, credential_id)
    if len({row["local_id"] for row in printers}) != len(printers):
        raise ValidationError("Repeated printer identity.")
    incoming = {row["local_id"] for row in printers}
    known = set(DiscoveredPrinter.objects.filter(agent=agent).values_list("local_id", flat=True))
    if len(incoming | known) > 500:
        raise ValidationError("Installation inventory limit reached.")
    now = timezone.now()
    # Retain identity/history, but absent queues must immediately stop claiming.
    DiscoveredPrinter.objects.filter(agent=agent).exclude(local_id__in=incoming).update(
        health="OFFLINE"
    )
    for row in printers:
        old = DiscoveredPrinter.objects.filter(agent=agent, local_id=row["local_id"]).first()
        if old and old.transport != row["transport"]:
            raise ValidationError("Discovery transport identity is immutable.")
        if old and any(getattr(old, key) != row[key] for key in ("queue_name", "driver_name")):
            AgentPrinterRoute.objects.filter(printer=old).update(
                enabled=False, raw_escpos_verified=False, version=F("version") + 1
            )
            record_audit_event(
                actor=ActorContext(agent.venue_id, None, None, agent.device_id),
                event_type="print.agent_route_invalidated",
                entity_type="DiscoveredPrinter",
                entity_id=str(old.id),
                metadata={"agent_id": str(agent.id), "reason": "Observed queue/driver changed"},
            )
        DiscoveredPrinter.objects.update_or_create(
            agent=agent, local_id=row["local_id"], defaults={**row, "last_seen_at": now}
        )
    return {"protocol_version": 1, "observed": len(printers)}


def printer_fingerprint(printer):
    return hashlib.sha256(
        repr((printer.queue_name, printer.driver_name, printer.transport)).encode()
    ).hexdigest()


def inventory(session):
    return {
        "printers": [
            {
                "id": str(p.id),
                "agent_id": str(p.agent_id),
                "local_id": p.local_id,
                "label": p.label,
                "queue_name": p.queue_name,
                "transport": p.transport,
                "driver_name": p.driver_name,
                "health": p.health,
                "last_seen_at": p.last_seen_at,
                "config_fingerprint": printer_fingerprint(p),
            }
            for p in DiscoveredPrinter.objects.filter(agent__venue_id=session.venue_id).order_by(
                "agent_id", "local_id"
            )[:500]
        ],
        "routes": [
            route_payload(r)
            for r in AgentPrinterRoute.objects.filter(endpoint__venue_id=session.venue_id).order_by(
                "id"
            )[:500]
        ],
    }


def route_payload(route):
    return {
        "id": str(route.id),
        "endpoint_id": str(route.endpoint_id),
        "printer_id": str(route.printer_id),
        "transport": route.transport,
        "profile_id": route.profile_id,
        "destination": route.destination,
        "port": route.port,
        "enabled": route.enabled,
        "version": route.version,
        "raw_escpos_verified": route.raw_escpos_verified,
    }


@transaction.atomic
def save_route(session, values):
    from modules.access.agent_credentials import authorize_manager

    printer = get_object_or_404(
        DiscoveredPrinter.objects.select_related("agent__device", "agent__venue"),
        pk=values["printer_id"],
        agent__venue_id=session.venue_id,
    )
    # Same lock order as machine claims/revocation, then endpoint/route/job.
    agent = (
        PrintAgent.objects.select_for_update(of=("self",))
        .select_related("device", "venue")
        .get(pk=printer.agent_id)
    )
    authorize_manager(session, agent)
    validate_agent(agent)
    printer = get_object_or_404(
        DiscoveredPrinter.objects.select_for_update(), pk=printer.pk, agent=agent
    )
    if values["printer_fingerprint"] != printer_fingerprint(printer):
        raise ValidationError("Printer observation changed; inspect it again before enabling.")
    endpoint = get_object_or_404(
        PrinterEndpoint.objects.select_for_update(),
        pk=values["endpoint_id"],
        venue_id=session.venue_id,
        adapter="AGENT",
    )
    route_id = values.get("id")
    if route_id:
        route = get_object_or_404(
            AgentPrinterRoute.objects.select_for_update(),
            pk=route_id,
            endpoint=endpoint,
            printer=printer,
        )
        if route.version != values["expected_version"]:
            raise ValidationError("Route configuration version conflict.")
        route.version += 1
    else:
        if values["expected_version"] != 0:
            raise ValidationError("New route requires version zero.")
        # Identity makes a lost create response recoverable by readback, not another route.
        if AgentPrinterRoute.objects.filter(endpoint=endpoint, printer=printer).exists():
            raise ValidationError("Route exists; reload its version before editing.")
        route = AgentPrinterRoute(endpoint=endpoint, printer=printer)
    for key in ("transport", "profile_id", "destination", "port", "enabled", "raw_escpos_verified"):
        setattr(route, key, values[key])
    if route.profile_id not in PROFILES:
        raise ValidationError("Unsupported v1 driver.")
    if not PROFILES[route.profile_id].raw:
        if route.transport != "WINDOWS_DRIVER":
            raise ValidationError("Rendered driver requires Windows rendering.")
    elif not route.raw_escpos_verified or route.transport not in ("WINDOWS_RAW", "TCP_LAN"):
        raise ValidationError("RAW requires explicit tested compatibility on this route.")
    if route.transport != "TCP_LAN" and route.destination != printer.queue_name:
        raise ValidationError("Route must use the observed service queue.")
    route.full_clean()
    route.save()
    record_audit_event(
        actor=ActorContext.from_session(session),
        event_type="print.agent_route_configured",
        entity_type="AgentPrinterRoute",
        entity_id=str(route.id),
        metadata=route_payload(route),
    )
    return route_payload(route)


@transaction.atomic
def claim(agent, credential_id):
    agent = locked_identity(agent, credential_id)
    recover_expired()
    if agent.state != "ONLINE" or agent.version not in ("0.3.0", "0.5.0"):
        return {"protocol_version": 1, "job": None}
    routes = (
        AgentPrinterRoute.objects.select_for_update(of=("self",))
        .select_related("endpoint", "printer")
        .filter(
            printer__agent=agent,
            enabled=True,
            endpoint__adapter="AGENT",
            endpoint__enabled=True,
            printer__last_seen_at__gt=timezone.now() - timedelta(seconds=90),
        )
        .exclude(printer__health="OFFLINE")
        .order_by("priority", "id")
    )
    for route in routes:
        if not supports(agent.version, route.profile_id) or (
            PROFILES[route.profile_id].raw and not route.raw_escpos_verified
        ):
            continue
        job = claim_job([route.endpoint_id], agent_delivery=True)
        if job is None:
            continue
        attempt = PrintAttempt.objects.get(job=job, token=job.attempt_token)
        attempt.agent, attempt.route, attempt.route_version = agent, route, route.version
        attempt.save(update_fields=["agent", "route", "route_version"])
        content = render_profile(
            route.profile_id, job.document, route.endpoint.width_mm, bool(job.reprint_of_id)
        )
        if len(content) > 262144:
            finish_attempt(
                job.id, job.attempt_token, "FAILED_FINAL", "Document exceeds agent payload limit"
            )
            continue
        return {
            "protocol_version": 1,
            "job": {
                "job_id": str(job.id),
                "attempt_token": str(job.attempt_token),
                "lease_until": job.lease_until,
                "lease_seconds": max(
                    0, int((job.lease_until - timezone.now()).total_seconds()) - 5
                ),
                "route_id": str(route.id),
                "route_version": route.version,
                "transport": route.transport,
                "destination": route.destination,
                "port": route.port,
                "profile_id": route.profile_id,
                "raw_escpos_verified": route.raw_escpos_verified,
                "width_mm": route.endpoint.width_mm,
                "content": base64.b64encode(content).decode(),
                "sha256": hashlib.sha256(content).hexdigest(),
            },
        }
    return {"protocol_version": 1, "job": None}


@transaction.atomic
def result(agent, credential_id, job_id, values):
    agent = locked_identity(agent, credential_id)
    # Match existing job lock -> attempt lock order, including recovery.
    job = get_object_or_404(
        PrintJob.objects.select_for_update(),
        pk=job_id,
        document__venue_id=agent.venue_id,
        endpoint__adapter="AGENT",
    )
    attempt = get_object_or_404(
        PrintAttempt,
        job=job,
        token=values["attempt_token"],
        agent=agent,
        route_id=values["route_id"],
        route_version=values["route_version"],
    )
    if attempt.finished_at:
        return {"accepted": attempt.outcome == values["outcome"], "state": job.state}
    accepted = finish_attempt(
        job.id,
        attempt.token,
        values["outcome"],
        "Agent transport result; physical output unconfirmed",
    )
    job.refresh_from_db()
    return {"accepted": accepted, "state": job.state}
