"""Authoritative host resolution. Forwarded host is never an authority."""

import re
from contextvars import ContextVar
from dataclasses import dataclass

from django.core.exceptions import ValidationError

RESERVED_LABELS = frozenset(
    {
        "api",
        "admin",
        "www",
        "bar",
        "cozinha",
        "cliente",
        "gerencia",
        "atendimento",
        "pedido",
        "app",
        "kitchen",
        "owner",
        "guest",
        "management",
        "staff",
        "cash",
        "reports",
        "mail",
        "static",
        "assets",
    }
)
HOST_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.rodada\.ai", re.ASCII)
resolved_venue_id = ContextVar("rodada_host_venue_id", default=None)


@dataclass(frozen=True)
class HostResolutionError(Exception):
    code: str = "VENUE_HOST_NOT_FOUND"
    status_code: int = 421


def normalize_hostname(hostname):
    if not isinstance(hostname, str):
        raise ValidationError("Invalid hostname")
    value = hostname.lower()
    if len(value) > 253 or not HOST_PATTERN.fullmatch(value):
        raise ValidationError("Unsupported or malformed establishment hostname")
    if value.split(".")[0] in RESERVED_LABELS:
        raise ValidationError("Reserved platform hostname")
    return value


def resolve_venue_from_hostname(hostname):
    from .models import VenueDomain

    try:
        hostname = normalize_hostname(hostname)
    except ValidationError as exc:
        raise HostResolutionError() from exc
    domain = (
        VenueDomain.objects.select_related("venue")
        .filter(hostname=hostname, is_active=True, is_verified=True)
        .first()
    )
    if domain is None:
        raise HostResolutionError()
    return domain.venue


def assert_staff_venue(venue_id):
    from modules.access.services import AccessServiceError

    expected = resolved_venue_id.get()
    if expected is not None and expected != venue_id:
        raise AccessServiceError(
            "VENUE_HOST_MISMATCH", "Sessão pertence a outro estabelecimento.", 403
        )


def assert_guest_venue(venue_id):
    from modules.guest_access.services import GuestAccessError

    expected = resolved_venue_id.get()
    if expected is not None and expected != venue_id:
        raise GuestAccessError("QR_NOT_FOUND", "QR inválido ou expirado.", 404)
