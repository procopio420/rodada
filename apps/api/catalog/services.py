from django.db import transaction
from django.utils import timezone

from catalog.models import CanonicalItem, Product
from dispatch.services import publish_venue_event


def canonical_matches(query):
    return CanonicalItem.objects.filter(name__icontains=query.strip()).order_by("name")[:12]


@transaction.atomic
def create_canonical_item(name, description=""):
    item, created = CanonicalItem.objects.get_or_create(name=name.strip(), defaults={"description": description})
    if created:
        item.ensure_fallback()
        item.save(update_fields=["icon_key"])
    return item, created


@transaction.atomic
def set_product_availability(product, available):
    product.available = available
    product.save(update_fields=["available"])
    publish_venue_event(product.venue_id, "catalog.availability_changed", {"product_id": product.id, "available": available})
    return product


def generate_pending_icons(limit=100):
    """Development provider: persists a deterministic icon key without external AI credentials."""
    for item in CanonicalItem.objects.filter(icon_status__in=["PENDING", "FAILED"]).order_by("id")[:limit]:
        item.ensure_fallback()
        item.icon_attempts += 1
        item.icon_status = "READY"
        item.icon_generated_at = timezone.now()
        item.save(update_fields=["icon_key", "icon_attempts", "icon_status", "icon_generated_at"])
