import hashlib
import secrets
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from modules.access.capabilities import effective_capabilities
from modules.access.context import ActorContext
from modules.access.invalidation import AccessInvalidationType, publish_access_invalidation
from modules.access.models import (
    DeviceRegistration,
    DeviceTrustState,
    MembershipStatus,
    PinLoginThrottle,
    StaffMember,
    StaffSession,
    VenueStaffMembership,
)
from modules.audit.models import AuditEvent
from modules.audit.services import record_audit_event
from modules.venue.models import Venue


@dataclass(frozen=True)
class AccessServiceError(Exception):
    code: str
    message: str
    status_code: int = 400
    retry_after_seconds: int | None = None


def _seconds_setting(name: str, default: int) -> int:
    return int(getattr(settings, name, default))


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def hash_installation_id(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _new_token(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(48)}"


def _audit(
    *,
    venue: Venue,
    event_type: str,
    actor_staff: StaffMember | None = None,
    actor_session: StaffSession | None = None,
    device: DeviceRegistration | None = None,
    metadata: dict | None = None,
) -> None:
    if actor_session is not None:
        record_audit_event(
            actor=ActorContext.from_session(actor_session),
            event_type=event_type,
            metadata=metadata,
        )
        return

    AuditEvent.objects.create(
        venue=venue,
        event_type=event_type,
        actor_staff=actor_staff,
        device=device,
        metadata=metadata or {},
    )


def _throttle_rows(
    *,
    venue: Venue,
    login_identifier: str,
    installation_key_hash: str,
):
    return PinLoginThrottle.objects.filter(
        venue=venue,
        login_identifier=login_identifier,
    ).filter(Q(installation_key_hash="") | Q(installation_key_hash=installation_key_hash))


def _retry_after_seconds(
    *,
    venue: Venue,
    login_identifier: str,
    installation_key_hash: str,
) -> int:
    now = timezone.now()
    blocked_until = None
    for row in _throttle_rows(
        venue=venue,
        login_identifier=login_identifier,
        installation_key_hash=installation_key_hash,
    ):
        if row.blocked_until and row.blocked_until > now:
            blocked_until = max(blocked_until or row.blocked_until, row.blocked_until)
    if not blocked_until:
        return 0
    return max(1, int((blocked_until - now).total_seconds()))


@transaction.atomic
def _register_pin_failure(
    *,
    venue: Venue,
    login_identifier: str,
    installation_key_hash: str,
) -> None:
    threshold = _seconds_setting("RODADA_PIN_FAILURE_THRESHOLD", 5)
    base_backoff = _seconds_setting("RODADA_PIN_BACKOFF_BASE_SECONDS", 15)
    max_backoff = _seconds_setting("RODADA_PIN_BACKOFF_MAX_SECONDS", 300)
    now = timezone.now()

    for scope_hash in ("", installation_key_hash):
        throttle, _ = PinLoginThrottle.objects.select_for_update().get_or_create(
            venue=venue,
            login_identifier=login_identifier,
            installation_key_hash=scope_hash,
        )
        throttle.failure_count += 1
        if throttle.failure_count >= threshold:
            exponent = throttle.failure_count - threshold
            delay = min(max_backoff, base_backoff * (2**exponent))
            throttle.blocked_until = now + timedelta(seconds=delay)
        throttle.save(update_fields=["failure_count", "blocked_until", "updated_at"])


def _clear_pin_failures(
    *,
    venue: Venue,
    login_identifier: str,
    installation_key_hash: str,
) -> None:
    _throttle_rows(
        venue=venue,
        login_identifier=login_identifier,
        installation_key_hash=installation_key_hash,
    ).delete()


def _session_failure(session: StaffSession) -> AccessServiceError | None:
    now = timezone.now()
    if session.revoked_at:
        return AccessServiceError("SESSION_REVOKED", "Sessão encerrada.", 401)
    if session.superseded_at:
        return AccessServiceError("SESSION_SUPERSEDED", "Sessão substituída.", 401)
    if session.expires_at <= now:
        return AccessServiceError("SESSION_EXPIRED", "Sessão expirada.", 401)
    if not session.staff_member.is_active:
        return AccessServiceError("STAFF_INACTIVE", "Acesso do operador desativado.", 403)
    if session.membership.status == MembershipStatus.REVOKED:
        return AccessServiceError("MEMBERSHIP_REVOKED", "Acesso ao estabelecimento revogado.", 403)
    if session.membership.status != MembershipStatus.ACTIVE:
        return AccessServiceError("MEMBERSHIP_SUSPENDED", "Acesso ao estabelecimento suspenso.", 403)
    if session.membership.venue_id != session.venue_id:
        return AccessServiceError("AUTH_REQUIRED", "Contexto de estabelecimento inválido.", 401)
    if session.device_id and session.device.trust_state == DeviceTrustState.REVOKED:
        return AccessServiceError("DEVICE_REVOKED", "Dispositivo revogado.", 403)
    return None


def session_for_access_token(raw_access_token: str) -> StaffSession:
    token_hash = hash_token(raw_access_token)
    session = (
        StaffSession.objects.select_related("venue", "staff_member", "membership", "device")
        .filter(access_token_hash=token_hash)
        .first()
    )
    if not session:
        raise AccessServiceError("AUTH_REQUIRED", "Token de acesso inválido.", 401)

    failure = _session_failure(session)
    if failure:
        raise failure

    now = timezone.now()
    if not session.access_expires_at or session.access_expires_at <= now:
        raise AccessServiceError("ACCESS_TOKEN_EXPIRED", "Token de acesso expirado.", 401)

    return session


def _issue_tokens(session: StaffSession) -> dict:
    now = timezone.now()
    access_token = _new_token("rat")
    refresh_token = _new_token("rrt")
    access_ttl = timedelta(seconds=_seconds_setting("RODADA_ACCESS_TOKEN_TTL_SECONDS", 900))
    access_expires_at = min(now + access_ttl, session.expires_at)

    session.access_token_hash = hash_token(access_token)
    session.refresh_token_hash = hash_token(refresh_token)
    session.access_expires_at = access_expires_at
    session.last_seen_at = now
    session.save(
        update_fields=[
            "access_token_hash",
            "refresh_token_hash",
            "access_expires_at",
            "last_seen_at",
        ]
    )

    return {
        "session_id": str(session.id),
        "access_token": access_token,
        "access_expires_at": access_expires_at,
        "refresh_token": refresh_token,
        "refresh_expires_at": session.expires_at,
    }


@transaction.atomic
def _complete_login(
    *,
    venue: Venue,
    staff: StaffMember,
    normalized_login: str,
    installation_key_hash: str,
    platform: str,
    friendly_label: str,
) -> dict:
    membership = (
        VenueStaffMembership.objects.select_for_update()
        .filter(venue=venue, staff_member=staff)
        .first()
    )
    if not membership:
        raise AccessServiceError("MEMBERSHIP_REQUIRED", "Sem acesso a este estabelecimento.", 403)
    if membership.status == MembershipStatus.REVOKED:
        raise AccessServiceError("MEMBERSHIP_REVOKED", "Acesso ao estabelecimento revogado.", 403)
    if membership.status != MembershipStatus.ACTIVE:
        raise AccessServiceError("MEMBERSHIP_SUSPENDED", "Acesso ao estabelecimento suspenso.", 403)
    if not staff.is_active:
        raise AccessServiceError("STAFF_INACTIVE", "Acesso do operador desativado.", 403)

    device, created = DeviceRegistration.objects.get_or_create(
        venue=venue,
        installation_key_hash=installation_key_hash,
        defaults={"platform": platform, "friendly_label": friendly_label},
    )
    if device.trust_state == DeviceTrustState.REVOKED:
        raise AccessServiceError("DEVICE_REVOKED", "Dispositivo revogado.", 403)

    changed = []
    if device.platform != platform:
        device.platform = platform
        changed.append("platform")
    if friendly_label and device.friendly_label != friendly_label:
        device.friendly_label = friendly_label
        changed.append("friendly_label")
    if not created:
        device.last_seen_at = timezone.now()
        changed.append("last_seen_at")
    if changed:
        device.save(update_fields=changed)

    _clear_pin_failures(
        venue=venue,
        login_identifier=normalized_login,
        installation_key_hash=installation_key_hash,
    )

    now = timezone.now()
    refresh_ttl = timedelta(seconds=_seconds_setting("RODADA_REFRESH_TOKEN_TTL_SECONDS", 43200))
    session = StaffSession.objects.create(
        venue=venue,
        staff_member=staff,
        membership=membership,
        device=device,
        expires_at=now + refresh_ttl,
    )
    tokens = _issue_tokens(session)

    _audit(
        venue=venue,
        event_type="auth.login_succeeded",
        actor_staff=staff,
        actor_session=session,
        device=device,
        metadata={"device_created": created},
    )

    return {
        **tokens,
        "staff": {"id": str(staff.id), "display_name": staff.display_name},
        "venue": {"id": str(venue.id), "slug": venue.slug, "name": venue.name},
        "role": membership.role,
        "capabilities": sorted(effective_capabilities(membership)),
        "device": {
            "id": str(device.id),
            "trust_state": device.trust_state,
            "platform": device.platform,
        },
    }


def authenticate_staff(
    *,
    venue_slug: str,
    login_identifier: str,
    pin: str,
    installation_id: str,
    platform: str,
    friendly_label: str = "",
) -> dict:
    venue = Venue.objects.filter(slug=venue_slug).first()
    if not venue:
        raise AccessServiceError("INVALID_CREDENTIALS", "Credenciais inválidas.", 401)

    normalized_login = login_identifier.strip().casefold()
    installation_key_hash = hash_installation_id(installation_id)

    staff = StaffMember.objects.filter(login_identifier__iexact=normalized_login).first()
    if not staff:
        _audit(
            venue=venue,
            event_type="auth.login_failed",
            metadata={"failure_class": "UNKNOWN_IDENTIFIER"},
        )
        raise AccessServiceError("INVALID_CREDENTIALS", "Credenciais inválidas.", 401)

    retry_after = _retry_after_seconds(
        venue=venue,
        login_identifier=normalized_login,
        installation_key_hash=installation_key_hash,
    )
    if retry_after:
        raise AccessServiceError(
            "AUTH_THROTTLED",
            "Muitas tentativas. Tente novamente em instantes.",
            429,
            retry_after,
        )

    if not staff.check_pin(pin):
        _register_pin_failure(
            venue=venue,
            login_identifier=normalized_login,
            installation_key_hash=installation_key_hash,
        )
        _audit(
            venue=venue,
            event_type="auth.login_failed",
            actor_staff=staff,
            metadata={"failure_class": "INVALID_PIN"},
        )
        raise AccessServiceError("INVALID_CREDENTIALS", "Credenciais inválidas.", 401)

    try:
        return _complete_login(
            venue=venue,
            staff=staff,
            normalized_login=normalized_login,
            installation_key_hash=installation_key_hash,
            platform=platform,
            friendly_label=friendly_label,
        )
    except AccessServiceError as exc:
        _audit(
            venue=venue,
            event_type="auth.login_failed",
            actor_staff=staff,
            metadata={"failure_class": exc.code},
        )
        raise


@transaction.atomic
def refresh_staff_session(raw_refresh_token: str) -> dict:
    token_hash = hash_token(raw_refresh_token)
    session = (
        StaffSession.objects.select_for_update()
        .select_related("venue", "staff_member", "membership", "device")
        .filter(refresh_token_hash=token_hash)
        .first()
    )
    if not session:
        raise AccessServiceError("AUTH_REQUIRED", "Refresh token inválido.", 401)

    failure = _session_failure(session)
    if failure:
        raise failure

    tokens = _issue_tokens(session)
    _audit(
        venue=session.venue,
        event_type="auth.session_refreshed",
        actor_staff=session.staff_member,
        actor_session=session,
        device=session.device,
    )
    return tokens


@transaction.atomic
def revoke_session(session: StaffSession, reason: str) -> None:
    locked = (
        StaffSession.objects.select_for_update()
        .select_related("venue", "staff_member", "device")
        .get(pk=session.pk)
    )
    if locked.revoked_at:
        return
    locked.revoked_at = timezone.now()
    locked.revocation_reason = reason
    locked.save(update_fields=["revoked_at", "revocation_reason"])
    publish_access_invalidation(
        session=locked,
        event_type=AccessInvalidationType.SESSION_REVOKED,
        reason=reason,
    )
    _audit(
        venue=locked.venue,
        event_type="auth.session_revoked",
        actor_staff=locked.staff_member,
        actor_session=locked,
        device=locked.device,
        metadata={"reason": reason},
    )



def recent_reauthentication_valid(session: StaffSession) -> bool:
    if not session.recently_reauthenticated_at:
        return False
    window = timedelta(seconds=_seconds_setting("RODADA_REAUTH_WINDOW_SECONDS", 300))
    return session.recently_reauthenticated_at >= timezone.now() - window


def record_reauth_required(session: StaffSession) -> None:
    _audit(
        venue=session.venue,
        event_type="auth.reauth_required",
        actor_staff=session.staff_member,
        actor_session=session,
        device=session.device,
    )


@transaction.atomic
def _complete_operator_switch(
    *,
    current_session_id,
    target_staff: StaffMember,
    normalized_login: str,
) -> dict:
    locked = (
        StaffSession.objects.select_for_update()
        .select_related("venue", "staff_member", "membership", "device")
        .get(pk=current_session_id)
    )
    failure = _session_failure(locked)
    if failure:
        raise failure
    if not locked.device_id or locked.device.trust_state != DeviceTrustState.TRUSTED:
        raise AccessServiceError(
            "TRUSTED_DEVICE_REQUIRED",
            "Troca rápida exige um dispositivo confiável.",
            403,
        )

    target_membership = (
        VenueStaffMembership.objects.select_for_update()
        .filter(venue=locked.venue, staff_member=target_staff)
        .first()
    )
    if not target_membership:
        raise AccessServiceError("MEMBERSHIP_REQUIRED", "Sem acesso a este estabelecimento.", 403)
    if target_membership.status == MembershipStatus.REVOKED:
        raise AccessServiceError("MEMBERSHIP_REVOKED", "Acesso ao estabelecimento revogado.", 403)
    if target_membership.status != MembershipStatus.ACTIVE:
        raise AccessServiceError("MEMBERSHIP_SUSPENDED", "Acesso ao estabelecimento suspenso.", 403)
    if not target_staff.is_active:
        raise AccessServiceError("STAFF_INACTIVE", "Acesso do operador desativado.", 403)

    _clear_pin_failures(
        venue=locked.venue,
        login_identifier=normalized_login,
        installation_key_hash=locked.device.installation_key_hash,
    )

    now = timezone.now()
    locked.superseded_at = now
    locked.save(update_fields=["superseded_at"])
    publish_access_invalidation(
        session=locked,
        event_type=AccessInvalidationType.SESSION_SUPERSEDED,
        reason="OPERATOR_SWITCH",
        metadata={"next_staff_id": str(target_staff.id)},
    )

    refresh_ttl = timedelta(seconds=_seconds_setting("RODADA_REFRESH_TOKEN_TTL_SECONDS", 43200))
    next_session = StaffSession.objects.create(
        venue=locked.venue,
        staff_member=target_staff,
        membership=target_membership,
        device=locked.device,
        expires_at=now + refresh_ttl,
    )
    tokens = _issue_tokens(next_session)

    _audit(
        venue=locked.venue,
        event_type="auth.operator_switched",
        actor_staff=target_staff,
        actor_session=next_session,
        device=locked.device,
        metadata={
            "previous_staff_id": str(locked.staff_member_id),
            "previous_session_id": str(locked.id),
        },
    )

    return {
        **tokens,
        "staff": {"id": str(target_staff.id), "display_name": target_staff.display_name},
        "role": target_membership.role,
        "capabilities": sorted(effective_capabilities(target_membership)),
        "device": {
            "id": str(locked.device.id),
            "trust_state": locked.device.trust_state,
            "platform": locked.device.platform,
        },
    }


def switch_operator(
    *,
    current_session: StaffSession,
    login_identifier: str,
    pin: str,
) -> dict:
    failure = _session_failure(current_session)
    if failure:
        raise failure
    if not current_session.device_id or current_session.device.trust_state != DeviceTrustState.TRUSTED:
        raise AccessServiceError(
            "TRUSTED_DEVICE_REQUIRED",
            "Troca rápida exige um dispositivo confiável.",
            403,
        )

    normalized_login = login_identifier.strip().casefold()
    target_staff = StaffMember.objects.filter(login_identifier__iexact=normalized_login).first()
    if not target_staff:
        raise AccessServiceError("INVALID_CREDENTIALS", "Credenciais inválidas.", 401)
    if target_staff.pk == current_session.staff_member_id:
        raise AccessServiceError(
            "OPERATOR_ALREADY_ACTIVE",
            "Este operador já está ativo.",
            409,
        )

    retry_after = _retry_after_seconds(
        venue=current_session.venue,
        login_identifier=normalized_login,
        installation_key_hash=current_session.device.installation_key_hash,
    )
    if retry_after:
        raise AccessServiceError(
            "AUTH_THROTTLED",
            "Muitas tentativas. Tente novamente em instantes.",
            429,
            retry_after,
        )

    if not target_staff.check_pin(pin):
        _register_pin_failure(
            venue=current_session.venue,
            login_identifier=normalized_login,
            installation_key_hash=current_session.device.installation_key_hash,
        )
        _audit(
            venue=current_session.venue,
            event_type="auth.operator_switch_failed",
            actor_staff=current_session.staff_member,
            actor_session=current_session,
            device=current_session.device,
            metadata={"failure_class": "INVALID_PIN"},
        )
        raise AccessServiceError("INVALID_CREDENTIALS", "Credenciais inválidas.", 401)

    return _complete_operator_switch(
        current_session_id=current_session.pk,
        target_staff=target_staff,
        normalized_login=normalized_login,
    )


@transaction.atomic
def _complete_reauthentication(session_id) -> dict:
    locked = (
        StaffSession.objects.select_for_update()
        .select_related("venue", "staff_member", "membership", "device")
        .get(pk=session_id)
    )
    failure = _session_failure(locked)
    if failure:
        raise failure

    login_identifier = locked.staff_member.login_identifier.strip().casefold()
    installation_key_hash = locked.device.installation_key_hash if locked.device_id else ""
    _clear_pin_failures(
        venue=locked.venue,
        login_identifier=login_identifier,
        installation_key_hash=installation_key_hash,
    )

    now = timezone.now()
    locked.recently_reauthenticated_at = now
    locked.save(update_fields=["recently_reauthenticated_at"])

    _audit(
        venue=locked.venue,
        event_type="auth.reauth_succeeded",
        actor_staff=locked.staff_member,
        actor_session=locked,
        device=locked.device,
    )

    window = timedelta(seconds=_seconds_setting("RODADA_REAUTH_WINDOW_SECONDS", 300))
    return {
        "reauthenticated_at": now,
        "valid_until": now + window,
    }


def reauthenticate_staff(*, session: StaffSession, pin: str) -> dict:
    failure = _session_failure(session)
    if failure:
        raise failure

    login_identifier = session.staff_member.login_identifier.strip().casefold()
    installation_key_hash = session.device.installation_key_hash if session.device_id else ""

    retry_after = _retry_after_seconds(
        venue=session.venue,
        login_identifier=login_identifier,
        installation_key_hash=installation_key_hash,
    )
    if retry_after:
        raise AccessServiceError(
            "AUTH_THROTTLED",
            "Muitas tentativas. Tente novamente em instantes.",
            429,
            retry_after,
        )

    if not session.staff_member.check_pin(pin):
        _register_pin_failure(
            venue=session.venue,
            login_identifier=login_identifier,
            installation_key_hash=installation_key_hash,
        )
        _audit(
            venue=session.venue,
            event_type="auth.reauth_failed",
            actor_staff=session.staff_member,
            actor_session=session,
            device=session.device,
            metadata={"failure_class": "INVALID_PIN"},
        )
        raise AccessServiceError("INVALID_CREDENTIALS", "Credenciais inválidas.", 401)

    return _complete_reauthentication(session.pk)


def _active_session_queryset_for_membership(membership: VenueStaffMembership):
    return StaffSession.objects.filter(
        membership=membership,
        revoked_at__isnull=True,
        superseded_at__isnull=True,
        expires_at__gt=timezone.now(),
    )


def _active_session_queryset_for_device(device: DeviceRegistration):
    return StaffSession.objects.filter(
        device=device,
        revoked_at__isnull=True,
        superseded_at__isnull=True,
        expires_at__gt=timezone.now(),
    )


@transaction.atomic
def update_membership_admin(
    *,
    actor_session: StaffSession,
    membership_id,
    expected_version: int,
    role: str | None = None,
    status: str | None = None,
    reason: str = "",
) -> VenueStaffMembership:
    membership = (
        VenueStaffMembership.objects.select_for_update()
        .select_related("venue", "staff_member")
        .filter(pk=membership_id, venue=actor_session.venue)
        .first()
    )
    if not membership:
        raise AccessServiceError("NOT_FOUND", "Vínculo de staff não encontrado.", 404)

    if membership.staff_member_id == actor_session.staff_member_id and role is not None:
        raise AccessServiceError(
            "SELF_ROLE_CHANGE_FORBIDDEN",
            "Altere sua própria função usando outro OWNER autorizado.",
            409,
        )

    if membership.version != expected_version:
        raise AccessServiceError(
            "VERSION_CONFLICT",
            "O vínculo foi alterado por outra operação.",
            409,
        )

    before = {
        "role": membership.role,
        "status": membership.status,
        "version": membership.version,
    }
    changed_fields: list[str] = []

    if role is not None and role != membership.role:
        membership.role = role
        changed_fields.append("role")

    if status is not None and status != membership.status:
        membership.status = status
        changed_fields.append("status")
        if status == MembershipStatus.REVOKED:
            membership.revoked_at = timezone.now()
            membership.revoked_by = actor_session.staff_member
            changed_fields.extend(["revoked_at", "revoked_by"])
        elif membership.revoked_at is not None:
            membership.revoked_at = None
            membership.revoked_by = None
            changed_fields.extend(["revoked_at", "revoked_by"])

    if not changed_fields:
        return membership

    membership.version += 1
    changed_fields.append("version")
    membership.save(update_fields=changed_fields)

    publish_access_invalidation(
        venue_id=membership.venue_id,
        staff_member_id=membership.staff_member_id,
        event_type=AccessInvalidationType.MEMBERSHIP_CHANGED,
        reason=reason,
        metadata={
            "role": membership.role,
            "status": membership.status,
            "version": membership.version,
        },
    )

    if status in (MembershipStatus.SUSPENDED, MembershipStatus.REVOKED):
        now = timezone.now()
        _active_session_queryset_for_membership(membership).update(
            revoked_at=now,
            revocation_reason=f"MEMBERSHIP_{status}",
        )

    _audit(
        venue=actor_session.venue,
        event_type="membership.role_changed" if role is not None else "membership.status_changed",
        actor_staff=actor_session.staff_member,
        actor_session=actor_session,
        device=actor_session.device,
        metadata={
            "membership_id": str(membership.id),
            "target_staff_id": str(membership.staff_member_id),
            "before": before,
            "after": {
                "role": membership.role,
                "status": membership.status,
                "version": membership.version,
            },
            "reason": reason,
        },
    )
    return membership


@transaction.atomic
def update_device_trust_admin(
    *,
    actor_session: StaffSession,
    device_id,
    trust_state: str,
    reason: str = "",
) -> DeviceRegistration:
    device = (
        DeviceRegistration.objects.select_for_update()
        .filter(pk=device_id, venue=actor_session.venue)
        .first()
    )
    if not device:
        raise AccessServiceError("NOT_FOUND", "Dispositivo não encontrado.", 404)

    if device.trust_state == DeviceTrustState.REVOKED and trust_state != DeviceTrustState.REVOKED:
        raise AccessServiceError(
            "DEVICE_REVOKED",
            "Dispositivo revogado não pode voltar a ser confiável.",
            409,
        )

    before = device.trust_state
    if before == trust_state:
        return device

    device.trust_state = trust_state
    fields = ["trust_state"]
    if trust_state == DeviceTrustState.REVOKED:
        device.revoked_at = timezone.now()
        device.revoked_by = actor_session.staff_member
        device.revocation_reason = reason
        fields.extend(["revoked_at", "revoked_by", "revocation_reason"])
    device.save(update_fields=fields)

    publish_access_invalidation(
        venue_id=device.venue_id,
        device_id=device.id,
        event_type=AccessInvalidationType.DEVICE_CHANGED,
        reason=reason,
        metadata={"trust_state": device.trust_state},
    )

    if trust_state == DeviceTrustState.REVOKED:
        now = timezone.now()
        _active_session_queryset_for_device(device).update(
            revoked_at=now,
            revocation_reason="DEVICE_REVOKED",
        )

    _audit(
        venue=actor_session.venue,
        event_type=(
            "auth.device_revoked"
            if trust_state == DeviceTrustState.REVOKED
            else "auth.device_trusted"
        ),
        actor_staff=actor_session.staff_member,
        actor_session=actor_session,
        device=actor_session.device,
        metadata={
            "target_device_id": str(device.id),
            "before": before,
            "after": trust_state,
            "reason": reason,
        },
    )
    return device


@transaction.atomic
def revoke_session_admin(
    *,
    actor_session: StaffSession,
    target_session_id,
    reason: str = "",
) -> StaffSession:
    target = (
        StaffSession.objects.select_for_update()
        .select_related("venue", "staff_member", "device")
        .filter(pk=target_session_id, venue=actor_session.venue)
        .first()
    )
    if not target:
        raise AccessServiceError("NOT_FOUND", "Sessão não encontrada.", 404)

    if target.revoked_at is None:
        target.revoked_at = timezone.now()
        target.revocation_reason = reason or "ADMIN_REVOKE"
        target.save(update_fields=["revoked_at", "revocation_reason"])
        publish_access_invalidation(
            session=target,
            event_type=AccessInvalidationType.SESSION_REVOKED,
            reason=target.revocation_reason,
        )

    _audit(
        venue=actor_session.venue,
        event_type="auth.session_revoked",
        actor_staff=actor_session.staff_member,
        actor_session=actor_session,
        device=actor_session.device,
        metadata={
            "target_session_id": str(target.id),
            "target_staff_id": str(target.staff_member_id),
            "reason": reason,
        },
    )
    return target
