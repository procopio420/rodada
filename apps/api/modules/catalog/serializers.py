from pathlib import PurePosixPath
from rest_framework import serializers
from modules.catalog.models import FulfillmentStation, normalize_product_name


class QuickProductInput(serializers.Serializer):
    name = serializers.CharField(max_length=160)
    price_cents = serializers.IntegerField(min_value=0, max_value=2147483647)
    fulfillment_station = serializers.ChoiceField(choices=FulfillmentStation.values)
    description = serializers.CharField(max_length=600, required=False, allow_blank=True, default="")
    category = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")


    def validate_name(self, value):
        normalized = normalize_product_name(value)
        if not normalized or len(normalized) > 180:
            raise serializers.ValidationError("Nome normalizado inválido ou muito longo.")
        return value


def icon_payload(product):
    icon = product.icon
    return {"id": str(icon.id), "source": icon.source, "status": icon.status,
            "published_asset_url": f"/catalog/assets/{icon.id}/{PurePosixPath(icon.published_asset).name}/" if icon.published_asset else icon.published_asset_url or None}


def product_payload(product):
    from modules.catalog.customization import ordering_schema
    return {"id": str(product.id), "name": product.name, "price_cents": product.price_cents,
            "description": product.description, "category": product.category,
            "normalized_name": product.normalized_name, "active": product.active,
            "fulfillment_station": product.fulfillment_station,
            "availability": product.availability.state, "icon": icon_payload(product),
            **ordering_schema(product)}
