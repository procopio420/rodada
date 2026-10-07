from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from audit.models import AuditEvent
from customers.models import Relationship, VenueRelationshipPolicy
from pos.models import Tab
from pos.services import exposure_cents


DEFAULT_LIMITS = {"VISITOR": 3000, "KNOWN": 8000, "REGULAR": 20000, "HOUSE": 50000, "RESTRICTED": 0}


def policy_limit(venue, status):
    policy = VenueRelationshipPolicy.objects.filter(venue=venue, status=status).first()
    return policy.operating_limit_cents if policy else DEFAULT_LIMITS[status]


def initial_limit(venue, customer=None):
    relationship = Relationship.objects.filter(venue=venue, customer=customer).first() if customer else None
    return policy_limit(venue, relationship.status if relationship else Relationship.Status.VISITOR)


@transaction.atomic
def override_limit(tab_id, actor, new_limit_cents, reason=""):
    tab = Tab.objects.select_for_update().select_related("venue").get(pk=tab_id)
    if actor.venue_id != tab.venue_id or not actor.can_manage_finance:
        raise PermissionDenied("Only a manager from this venue can override a limit.")
    if new_limit_cents < 0:
        raise ValidationError("Operating limit cannot be negative.")
    before = tab.operating_limit_cents
    tab.operating_limit_cents = new_limit_cents
    tab.limit_overridden_by = actor
    tab.limit_overridden_at = timezone.now()
    tab.limit_override_reason = reason
    if tab.status == Tab.Status.REQUIRES_ACTION and exposure_cents(tab) < new_limit_cents:
        tab.status = Tab.Status.OPEN
    tab.save(update_fields=["operating_limit_cents", "limit_overridden_by", "limit_overridden_at", "limit_override_reason", "status"])
    AuditEvent.objects.create(venue=tab.venue, actor=actor, action="tab.limit_overridden", entity_type=tab._meta.label,
        entity_id=tab.id, reason=reason, before={"operating_limit_cents": before}, after={"operating_limit_cents": new_limit_cents})
    return tab
