"""Hostname registry lookup. Never select a default Venue on a miss."""

from django.core.exceptions import ValidationError

from .hostnames import normalize_tenant_hostname
from .models import VenueDomain


def resolve_venue_domain(hostname: str):
    """Return the verified, active Venue for a canonical public hostname.

    Caller must independently bind sessions and authorization to this Venue.
    """
    try:
        canonical = normalize_tenant_hostname(hostname)
    except ValidationError:
        return None
    return (
        VenueDomain.objects.select_related("venue")
        .filter(hostname=canonical, is_active=True, is_verified=True)
        .first()
    )
