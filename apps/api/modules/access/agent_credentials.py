"""Scoped machine credential lifecycle. Pairing UI/PoP is delivered in S2."""

import hashlib
import secrets
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

from modules.access.capabilities import Capability, has_capability
from modules.access.context import ActorContext
from modules.access.models import AgentCredential, DeviceTrustState, StaffSession
from modules.audit.services import record_audit_event
from modules.documents_printing.agent_contracts import PRINT_SCOPE
from modules.documents_printing.models import PrintAgent
from modules.venue.hostnames import resolved_venue_id


def token_digest(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def authorize_manager(session: StaffSession, agent: PrintAgent) -> None:
    if not isinstance(session, StaffSession) or not session.is_valid:
        raise PermissionDenied("Valid staff session required.")
    if session.venue_id != agent.venue_id or not has_capability(
        session.membership, Capability.PRINT_MANAGE
    ):
        raise PermissionDenied("Print management required in the agent's Venue.")


def validate_agent(agent: PrintAgent) -> None:
    if (
        not agent.venue_id
        or not agent.device_id
        or not agent.paired_at
        or agent.device.venue_id != agent.venue_id
        or agent.revoked_at
        or agent.device.revoked_at
        or agent.device.trust_state != DeviceTrustState.TRUSTED
    ):
        raise AuthenticationFailed("Agent authorization unavailable.")
    if not agent.venue.print_agents_enabled:
        raise PermissionDenied("Print agents disabled for this Venue.")


@transaction.atomic
def issue_credential(
    *, agent_id, session: StaffSession, rotate: bool = False, _raw_token: str | None = None
) -> str:
    agent = (
        PrintAgent.objects.select_for_update(of=("self",))
        .select_related("device", "venue")
        .get(pk=agent_id)
    )
    authorize_manager(session, agent)
    validate_agent(agent)
    active = AgentCredential.objects.filter(agent=agent, revoked_at__isnull=True)
    if active.exists() and not rotate:
        raise ValidationError("Rotate explicitly; an active credential already exists.")
    active.update(revoked_at=timezone.now())
    raw = _raw_token or ("rpa_" + secrets.token_urlsafe(32))
    if not raw.startswith("rpa_") or len(raw) != 47:
        raise ValidationError("Invalid machine credential format.")
    credential = AgentCredential.objects.create(
        agent=agent,
        token_hash=token_digest(raw),
        expires_at=timezone.now() + timedelta(days=30),
    )
    record_audit_event(
        actor=ActorContext.from_session(session),
        event_type="print.agent_credential_rotated" if rotate else "print.agent_credential_issued",
        entity_type="PrintAgent",
        entity_id=str(agent.id),
        metadata={"credential_id": str(credential.id), "scope": PRINT_SCOPE},
    )
    return raw


@transaction.atomic
def revoke_agent(*, agent_id, session: StaffSession, reason: str) -> PrintAgent:
    if not reason.strip() or len(reason) > 240:
        raise ValidationError("A bounded revocation reason is required.")
    agent = (
        PrintAgent.objects.select_for_update(of=("self",))
        .select_related("device", "venue")
        .get(pk=agent_id)
    )
    authorize_manager(session, agent)
    if agent.revoked_at:
        return agent
    now = timezone.now()
    agent.revoked_at = now
    agent.save(update_fields=["revoked_at"])
    AgentCredential.objects.filter(agent=agent, revoked_at__isnull=True).update(revoked_at=now)
    # Retain all delivery history. Future in-flight attempt recovery stays in Spec 015.
    agent.device.trust_state = DeviceTrustState.REVOKED
    agent.device.revoked_at = now
    agent.device.revoked_by = session.staff_member
    agent.device.revocation_reason = reason
    agent.device.save(
        update_fields=["trust_state", "revoked_at", "revoked_by", "revocation_reason"]
    )
    record_audit_event(
        actor=ActorContext.from_session(session),
        event_type="print.agent_revoked",
        entity_type="PrintAgent",
        entity_id=str(agent.id),
        reason=reason,
    )
    return agent


class PrintAgentAuthentication(BaseAuthentication):
    """Only installed on machine endpoints. Never added to DRF global defaults."""

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if len(parts) != 2 or parts[0].lower() != b"bearer":
            raise AuthenticationFailed("Invalid agent authorization.")
        try:
            raw = parts[1].decode("ascii")
        except UnicodeError as exc:
            raise AuthenticationFailed("Invalid agent authorization.") from exc
        if not raw.startswith("rpa_") or len(raw) != 47:
            raise AuthenticationFailed("Invalid agent authorization.")
        credential = (
            AgentCredential.objects.select_related("agent__device", "agent__venue")
            .filter(
                token_hash=token_digest(raw),
                revoked_at__isnull=True,
                expires_at__gt=timezone.now(),
                scope=PRINT_SCOPE,
            )
            .first()
        )
        if credential is None:
            raise AuthenticationFailed("Invalid agent authorization.")
        validate_agent(credential.agent)
        expected_venue = resolved_venue_id.get()
        if expected_venue is not None and str(expected_venue) != str(credential.agent.venue_id):
            raise PermissionDenied("Agent belongs to another Venue.")
        return credential.agent, credential

    def authenticate_header(self, request):
        return "Bearer"
