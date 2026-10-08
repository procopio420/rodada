from django.db import transaction
from rest_framework import serializers

from modules.audit.services import record_audit_event
from modules.catalog.models import Product, ProductIcon, normalize_product_name
from modules.venue.models import Venue


class ResolveProductInput(serializers.Serializer):
    name = serializers.CharField(max_length=160)
    price_cents = serializers.IntegerField(min_value=0, max_value=100_000_000)
    fulfillment_station = serializers.ChoiceField(choices=["BAR", "KITCHEN"])

    def validate_name(self, value):
        if not normalize_product_name(value) or len(normalize_product_name(value)) > 180:
            raise serializers.ValidationError("Nome normalizado inválido ou muito longo.")
        return value


def product_payload(product):
    icon = getattr(product, "icon", None)
    return {"id": str(product.id), "name": product.name, "price_cents": product.price_cents,
            "active": product.active, "fulfillment_station": product.fulfillment_station,
            "availability": product.availability.state,
            "icon": {"product_id": str(product.id), "status": icon.status if icon else "FAILED",
                     "source": icon.source if icon else "NONE",
                     "asset_url": icon.published_asset_url if icon else "",
                     "style_version": icon.style_version if icon else "rodada-icon-v1"}}


@transaction.atomic
def resolve_or_create_product(*, actor, name, price_cents, fulfillment_station):
    # One venue row is the creation mutex, including the absent-name race.
    Venue.objects.select_for_update().get(pk=actor.venue_id)
    product, created = Product.objects.get_or_create(
        venue_id=actor.venue_id, normalized_name=normalize_product_name(name),
        defaults={"name": name.strip(), "price_cents": price_cents,
                  "fulfillment_station": fulfillment_station},
    )
    ProductIcon.objects.get_or_create(product=product)
    if created:
        record_audit_event(actor=actor, event_type="catalog.product_created", entity_type="Product",
                          entity_id=str(product.id), metadata={"name": product.name,
                          "price_cents": price_cents, "station": fulfillment_station,
                          "icon_status": product.icon.status})
    return product, created
