"""Privileged provisioning only; no public domain onboarding endpoint."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .hostnames import normalize_hostname
from .models import Venue, VenueDomain


@transaction.atomic
def configure_domain(
    *, venue_id, hostname, is_primary=False, is_active=False, is_verified=False, actor=None, reason
):
    from modules.audit.models import AuditEvent
    from modules.audit.services import record_audit_event

    if not reason.strip():
        raise ValidationError("Domain changes require an audit reason")
    venue = Venue.objects.select_for_update().get(pk=venue_id)
    hostname = normalize_hostname(hostname)
    domain = VenueDomain.objects.select_for_update().filter(hostname=hostname).first()
    if domain and domain.venue_id != venue.pk:
        raise ValidationError("Hostname already belongs to another Venue")
    if is_primary and not (is_active and is_verified):
        raise ValidationError("Primary hostname must be active and verified")
    before = list(
        VenueDomain.objects.filter(venue=venue).values(
            "hostname", "is_primary", "is_active", "is_verified"
        )
    )
    if is_primary:
        VenueDomain.objects.filter(venue=venue, is_primary=True).exclude(hostname=hostname).update(
            is_primary=False, updated_at=timezone.now()
        )
    if domain is None:
        domain = VenueDomain(venue=venue, hostname=hostname)
    domain.is_primary, domain.is_active, domain.is_verified = is_primary, is_active, is_verified
    domain.full_clean()
    domain.save()
    metadata = {
        "before": before,
        "after": {
            "hostname": hostname,
            "is_primary": is_primary,
            "is_active": is_active,
            "is_verified": is_verified,
        },
    }
    if actor:
        if actor.venue_id != venue.pk:
            raise ValidationError("Actor belongs to another Venue")
        record_audit_event(
            actor=actor,
            event_type="venue.domain_configured",
            entity_type="VenueDomain",
            entity_id=str(domain.pk),
            reason=reason,
            metadata=metadata,
        )
    else:
        AuditEvent.objects.create(
            venue=venue,
            event_type="venue.domain_configured",
            entity_type="VenueDomain",
            entity_id=str(domain.pk),
            reason=reason,
            metadata=metadata,
        )
    return domain
