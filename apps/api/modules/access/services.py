import hashlib
import secrets
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from modules.access.capabilities import effective_capabilities
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
    AuditEvent.objects.create(
        venue=venue,
        event_type=event_type,
        actor_staff=actor_staff,
        actor_session=actor_session,
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
    _audit(
        venue=locked.venue,
        event_type="auth.session_revoked",
        actor_staff=locked.staff_member,
        actor_session=locked,
        device=locked.device,
        metadata={"reason": reason},
    )
