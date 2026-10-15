"""Atomic single-use manager approval and recoverable proof-of-possession delivery."""

import base64
import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    PermissionDenied,
    Throttled,
    ValidationError,
)

from modules.access.agent_credentials import issue_credential, token_digest, validate_agent
from modules.access.capabilities import Capability, has_capability
from modules.access.context import ActorContext
from modules.access.models import AgentCredential, DeviceRegistration, StaffSession
from modules.audit.services import record_audit_event
from modules.venue.models import Venue

from .models import PrintAgent, PrintAgentThrottle, PrintPairingRequest


class PairingExpired(APIException):
    status_code = 410
    default_detail = "Pairing recovery expired."


class InstallationPaired(APIException):
    status_code = 409
    default_detail = "Installation already paired; explicit local reset required."


class PairingUnavailable(APIException):
    status_code = 503
    default_detail = "Pairing unavailable: configure a dedicated pairing key."


def pairing_key() -> bytes:
    key = settings.RODADA_AGENT_PAIRING_SECRET
    if len(key) < 32:
        raise PairingUnavailable()
    return key.encode()


def derive(request: PrintPairingRequest, purpose: str) -> bytes:
    message = f"{purpose}:{request.id}:{request.proof_hash}".encode()
    return hmac.new(pairing_key(), message, hashlib.sha256).digest()


def display_code(request: PrintPairingRequest) -> str:
    return base64.b32encode(derive(request, "display")).decode()[:16]


def credential_token(request: PrintPairingRequest) -> str:
    return "rpa_" + base64.urlsafe_b64encode(derive(request, "credential")).decode().rstrip("=")


@transaction.atomic
def throttle(key: str, limit: int, seconds: int = 300) -> None:
    now = timezone.now()
    bucket, _ = PrintAgentThrottle.objects.get_or_create(
        key_hash=token_digest(key),
        defaults={"window_started_at": now},
    )
    bucket = PrintAgentThrottle.objects.select_for_update().get(pk=bucket.pk)
    if bucket.window_started_at + timedelta(seconds=seconds) <= now:
        bucket.window_started_at, bucket.count = now, 0
    bucket.count += 1
    bucket.save(update_fields=["window_started_at", "count"])
    # Raise outside the atomic call so rejected requests remain counted.


def enforce_throttle(key: str, limit: int, seconds: int = 300) -> None:
    throttle(key, limit, seconds)
    bucket = PrintAgentThrottle.objects.get(pk=token_digest(key))
    if bucket.count > limit:
        raise Throttled(wait=seconds)


def require_manager(session: StaffSession) -> None:
    if (
        not isinstance(session, StaffSession)
        or not session.is_valid
        or not has_capability(session.membership, Capability.PRINT_MANAGE)
    ):
        raise PermissionDenied("Print management required.")


@transaction.atomic
def start_pairing(*, installation_id, label: str, proof: str) -> dict:
    pairing_key()
    agent, _ = PrintAgent.objects.get_or_create(
        installation_id=installation_id,
        defaults={"label": label, "installation_proof_hash": token_digest(proof)},
    )
    agent = PrintAgent.objects.select_for_update().get(pk=agent.pk)
    if agent.installation_proof_hash and not secrets.compare_digest(
        agent.installation_proof_hash, token_digest(proof)
    ):
        raise AuthenticationFailed("Installation proof mismatch.")
    if not agent.installation_proof_hash:
        agent.installation_proof_hash = token_digest(proof)
        agent.save(update_fields=["installation_proof_hash"])
    if agent.paired_at or agent.revoked_at:
        raise InstallationPaired()
    last = PrintPairingRequest.objects.filter(agent=agent).order_by("-created_at").first()
    proof_hash = token_digest(proof)
    if last and not secrets.compare_digest(last.proof_hash, proof_hash):
        raise AuthenticationFailed("Installation proof mismatch.")
    if last and last.expires_at > timezone.now():
        request = last
    else:
        request = PrintPairingRequest(
            agent=agent, proof_hash=proof_hash, expires_at=timezone.now() + timedelta(minutes=10)
        )
        request.code_hash = token_digest(display_code(request))
        request.save()
    return {
        "request_id": str(request.id),
        "code": display_code(request),
        "installation_id": str(agent.installation_id),
        "label": agent.label,
        "expires_at": request.expires_at,
        "protocol_version": 1,
    }


def find_code(code: str) -> PrintPairingRequest:
    request = (
        PrintPairingRequest.objects.select_related("agent")
        .filter(
            code_hash=token_digest(code.upper()),
            consumed_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .first()
    )
    if not request:
        raise ValidationError("Pairing code invalid, consumed or expired.")
    return request


def inspect_pairing(*, code: str, session: StaffSession) -> dict:
    require_manager(session)
    request = find_code(code)
    return {
        "installation_id": str(request.agent.installation_id),
        "label": request.agent.label,
        "expires_at": request.expires_at,
        "venue_id": str(session.venue_id),
        "venue_name": session.venue.name,
    }


@transaction.atomic
def approve_pairing(*, code: str, installation_id, session: StaffSession) -> dict:
    require_manager(session)
    pairing_key()
    pending = find_code(code)
    agent = PrintAgent.objects.select_for_update().get(pk=pending.agent_id)
    request = PrintPairingRequest.objects.select_for_update().get(pk=pending.id)
    venue = Venue.objects.select_for_update().get(pk=session.venue_id)
    if not venue.print_agents_enabled:
        raise PermissionDenied("Print agents disabled for this Venue.")
    if request.consumed_at or request.expires_at <= timezone.now() or agent.paired_at:
        raise ValidationError("Pairing already consumed or expired.")
    if agent.installation_id != installation_id:
        raise ValidationError("Confirm the requesting installation.")
    device = DeviceRegistration.objects.create(
        venue=venue,
        installation_key_hash=token_digest("print-agent:" + str(agent.installation_id)),
        platform="WINDOWS",
        friendly_label=agent.label,
        trust_state="TRUSTED",
    )
    agent.venue, agent.device, agent.paired_at = venue, device, timezone.now()
    agent.save(update_fields=["venue", "device", "paired_at"])
    request.consumed_at, request.approved_by, request.approved_venue = (
        timezone.now(),
        session.staff_member,
        venue,
    )
    request.save(update_fields=["consumed_at", "approved_by", "approved_venue"])
    raw = issue_credential(agent_id=agent.id, session=session, _raw_token=credential_token(request))
    request.credential = agent.credentials.get(token_hash=token_digest(raw))
    request.save(update_fields=["credential"])
    record_audit_event(
        actor=ActorContext.from_session(session),
        event_type="print.agent_paired",
        entity_type="PrintAgent",
        entity_id=str(agent.id),
    )
    return {"agent_id": str(agent.id), "label": agent.label, "venue_id": str(venue.id)}


@transaction.atomic
def pairing_status(*, request_id, proof: str) -> dict:
    request = (
        PrintPairingRequest.objects.select_related("agent__device", "agent__venue", "credential")
        .filter(pk=request_id)
        .first()
    )
    if not request:
        # Expired unconsumed requests can be removed while an installation is offline.
        # Bootstrap still proves the immutable installation identity before renewal.
        raise PairingExpired()
    if not secrets.compare_digest(request.proof_hash, token_digest(proof)):
        raise AuthenticationFailed("Invalid pairing proof.")
    # Match activation/approval lock ordering; no stale pre-ACK credential response.
    agent = (
        PrintAgent.objects.select_for_update(of=("self",))
        .select_related("device", "venue")
        .get(pk=request.agent_id)
    )
    request = (
        PrintPairingRequest.objects.select_for_update(of=("self",))
        .select_related("credential")
        .get(pk=request.pk)
    )
    if not request.consumed_at:
        if request.expires_at <= timezone.now():
            raise PairingExpired()
        return {"state": "PENDING_PAIRING"}
    validate_agent(agent)
    if request.activated_at:
        return {"state": "PAIRED", "agent_id": str(request.agent_id)}
    if request.consumed_at + timedelta(minutes=10) <= timezone.now():
        raise PairingExpired()
    credential = request.credential
    if not credential or credential.revoked_at or credential.expires_at <= timezone.now():
        raise AuthenticationFailed("Pairing credential unavailable.")
    raw = credential_token(request)
    if not secrets.compare_digest(token_digest(raw), credential.token_hash):
        raise AuthenticationFailed("Pairing credential unavailable.")
    return {
        "state": "APPROVED",
        "credential": raw,
        "agent_id": str(request.agent_id),
        "venue_id": str(request.agent.venue_id),
        "credential_expires_at": credential.expires_at,
    }


@transaction.atomic
def activate(agent: PrintAgent, credential_id) -> dict:
    locked = (
        PrintAgent.objects.select_for_update(of=("self",))
        .select_related("device", "venue")
        .get(pk=agent.pk)
    )
    validate_agent(locked)
    if not AgentCredential.objects.filter(
        pk=credential_id, agent=locked, revoked_at__isnull=True, expires_at__gt=timezone.now()
    ).exists():
        raise AuthenticationFailed("Credential expired or revoked.")
    PrintPairingRequest.objects.filter(
        agent=locked, activated_at__isnull=True, consumed_at__isnull=False
    ).update(activated_at=timezone.now())
    return {"state": "PAIRED"}


@transaction.atomic
def heartbeat(agent: PrintAgent, version: str, credential_id) -> dict:
    locked = (
        PrintAgent.objects.select_for_update(of=("self",))
        .select_related("device", "venue")
        .get(pk=agent.pk)
    )
    validate_agent(locked)
    if not AgentCredential.objects.filter(
        pk=credential_id, agent=locked, revoked_at__isnull=True, expires_at__gt=timezone.now()
    ).exists():
        raise AuthenticationFailed("Credential expired or revoked.")
    from .agent_delivery import delivery_enabled

    locked.last_seen_at, locked.version = timezone.now(), version
    locked.save(update_fields=["last_seen_at", "version"])
    return {
        "protocol_version": 1,
        "agent_id": str(locked.id),
        "state": locked.state,
        "delivery_enabled": delivery_enabled(locked),
        "heartbeat_after_seconds": 10,
    }


@transaction.atomic
def set_enabled(*, session: StaffSession, enabled: bool) -> dict:
    require_manager(session)
    if enabled:
        pairing_key()
    venue = Venue.objects.select_for_update().get(pk=session.venue_id)
    before = venue.print_agents_enabled
    venue.print_agents_enabled = enabled
    venue.save(update_fields=["print_agents_enabled"])
    if before != enabled:
        record_audit_event(
            actor=ActorContext.from_session(session),
            event_type="print.agents_enabled_changed",
            entity_type="Venue",
            entity_id=str(venue.pk),
            metadata={"before": before, "after": enabled},
        )
    return {"enabled": enabled}
