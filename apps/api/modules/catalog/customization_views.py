from typing import ClassVar

from django.db import transaction
from django.db.models import F
from django.http import Http404
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability, has_capability
from modules.access.errors import AccessPermissionDenied
from modules.access.permissions import RequireCapability
from modules.audit.services import record_audit_event
from modules.catalog.customization import ordering_schema
from modules.catalog.models import (
    AvailabilityState,
    ModifierGroup,
    ModifierOption,
    Product,
    ProductModifierGroup,
    ProductVariant,
)


class VariantInput(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ("name", "price_cents", "active", "is_default", "sort_order")
        extra_kwargs: ClassVar[dict] = {"price_cents": {"min_value": 0, "max_value": 2147483647}}


class GroupInput(serializers.ModelSerializer):
    class Meta:
        model = ModifierGroup
        fields = ("name", "selection_mode", "min_selections", "max_selections", "active")

    def validate(self, values):
        minimum = values.get("min_selections", getattr(self.instance, "min_selections", 0))
        maximum = values.get("max_selections", getattr(self.instance, "max_selections", 1))
        mode = values.get("selection_mode", getattr(self.instance, "selection_mode", "SINGLE"))
        if not 0 <= minimum <= maximum <= 100 or maximum < 1 or (mode == "SINGLE" and maximum != 1):
            raise serializers.ValidationError("Regras de seleção inválidas.")
        return values


class OptionInput(serializers.ModelSerializer):
    class Meta:
        model = ModifierOption
        fields = (
            "name",
            "price_delta_cents",
            "active",
            "default_selected",
            "semantic_kind",
            "sort_order",
        )
        extra_kwargs: ClassVar[dict] = {
            "price_delta_cents": {"min_value": 0, "max_value": 2147483647}
        }


class CommandInput(serializers.Serializer):
    kind = serializers.ChoiceField(choices=["variant", "group", "option", "attach", "detach"])
    id = serializers.UUIDField(required=False)
    group_id = serializers.UUIDField(required=False)
    expected_version = serializers.IntegerField(min_value=1, required=False)
    display_order = serializers.IntegerField(min_value=0, required=False)
    values = serializers.DictField(default=dict)


class CustomizationView(APIView):
    permission_classes = (IsAuthenticated, RequireCapability)
    required_capability = Capability.CATALOG_CUSTOMIZATION_MANAGE

    def get(self, request, product_id):
        product = Product.objects.filter(pk=product_id, venue_id=request.auth.venue_id).first()
        if not product:
            raise Http404
        return Response(
            {
                **ordering_schema(product, include_inactive=True),
                "reusable_groups": list(
                    ModifierGroup.objects.filter(venue_id=request.auth.venue_id).values(
                        "id", "name"
                    )
                ),
            }
        )

    @transaction.atomic
    def post(self, request, product_id):
        command = CommandInput(data=request.data)
        command.is_valid(raise_exception=True)
        data = command.validated_data
        # Rare management edits lock the Venue's Products in deterministic order.
        # This serializes reusable group edits/attachment with all confirmations.
        products = list(
            Product.objects.select_for_update()
            .filter(venue_id=request.auth.venue_id)
            .order_by("id")
        )
        product = next((p for p in products if p.id == product_id), None)
        if not product:
            raise Http404
        before = ordering_schema(product, include_inactive=True)
        kind = data["kind"]
        group = None
        if kind in ("option", "attach", "detach"):
            group = ModifierGroup.objects.filter(
                pk=data.get("group_id"), venue_id=request.auth.venue_id
            ).first()
            if not group:
                raise Http404
        if kind in ("attach", "detach"):
            if kind == "detach":
                ProductModifierGroup.objects.filter(product=product, group=group).delete()
            else:

                class LinkInput(serializers.Serializer):
                    sort_order = serializers.IntegerField(min_value=0, default=0)

                values = LinkInput(data=data["values"])
                values.is_valid(raise_exception=True)
                ProductModifierGroup.objects.update_or_create(
                    product=product, group=group, defaults=values.validated_data
                )
            entity = group
        else:
            model, serializer, scope = {
                "variant": (ProductVariant, VariantInput, {"product": product}),
                "group": (ModifierGroup, GroupInput, {"venue_id": request.auth.venue_id}),
                "option": (ModifierOption, OptionInput, {"group": group}),
            }[kind]
            instance = (
                model.objects.filter(pk=data["id"], **scope).first() if data.get("id") else None
            )
            if data.get("id") and not instance:
                raise Http404
            if instance and data.get("expected_version") != instance.version:
                return Response(
                    {
                        "code": "CATALOG_VERSION_STALE",
                        "message": "Configuração mudou. Atualize antes de salvar.",
                    },
                    status=409,
                )
            values = serializer(instance, data=data["values"], partial=instance is not None)
            values.is_valid(raise_exception=True)
            if kind == "variant" and values.validated_data.get("is_default"):
                ProductVariant.objects.filter(product=product, is_default=True).exclude(
                    pk=getattr(instance, "pk", None)
                ).update(is_default=False, version=F("version") + 1)
            entity = values.save(**scope, version=instance.version + 1 if instance else 1)
            if kind == "group" and not instance:
                ProductModifierGroup.objects.create(product=product, group=entity)
        if kind == "group" and "display_order" in data:
            ProductModifierGroup.objects.filter(product=product, group=entity).update(
                sort_order=data["display_order"]
            )
        record_audit_event(
            actor=request.actor_context,
            event_type="catalog.customization_configured",
            entity_type=entity.__class__.__name__,
            entity_id=str(entity.pk),
            metadata={
                "product_id": str(product.id),
                "kind": kind,
                "values": data["values"],
                "before": before,
                "after": ordering_schema(product, include_inactive=True),
            },
        )
        return Response(
            {
                "id": str(entity.pk),
                "version": entity.version,
                **ordering_schema(product, include_inactive=True),
            }
        )


class ChoiceAvailabilityView(APIView):
    permission_classes = (IsAuthenticated, RequireCapability)
    required_capability = Capability.CATALOG_AVAILABILITY_MANAGE_STATION

    @transaction.atomic
    def post(self, request, product_id, kind, choice_id):
        class Input(serializers.Serializer):
            state = serializers.ChoiceField(choices=AvailabilityState.values)
            expected_version = serializers.IntegerField(min_value=1)
            reason = serializers.CharField(max_length=240, default="", allow_blank=True)

        values = Input(data=request.data)
        values.is_valid(raise_exception=True)
        data = values.validated_data
        products = list(
            Product.objects.select_for_update()
            .filter(venue_id=request.auth.venue_id)
            .order_by("id")
        )
        product = next((p for p in products if p.pk == product_id), None)
        if not product:
            raise Http404
        if kind == "variant":
            choice = ProductVariant.objects.filter(pk=choice_id, product=product).first()
            affected = [product]
        elif kind == "option":
            choice = ModifierOption.objects.filter(
                pk=choice_id,
                group__venue_id=request.auth.venue_id,
                group__product_links__product=product,
            ).first()
            affected = [
                p
                for p in products
                if choice and p.modifier_links.filter(group_id=choice.group_id).exists()
            ]
        else:
            raise Http404
        if not choice:
            raise Http404
        for p in affected:
            capability = "catalog.availability." + p.fulfillment_station.lower()
            if not has_capability(request.auth.membership, capability):
                raise AccessPermissionDenied(
                    "CAPABILITY_REQUIRED",
                    "Sem permissão de disponibilidade nesta estação.",
                    capability=capability,
                )
        if choice.version != data["expected_version"]:
            return Response(
                {
                    "code": "CATALOG_VERSION_STALE",
                    "message": "Disponibilidade mudou. Atualize a estação.",
                },
                status=409,
            )
        before = choice.availability
        choice.availability = data["state"]
        choice.version += 1
        choice.save(update_fields=["availability", "version"])
        record_audit_event(
            actor=request.actor_context,
            event_type=f"catalog.{kind}_availability_changed",
            entity_type=choice.__class__.__name__,
            entity_id=str(choice.pk),
            metadata={
                "before": before,
                "after": choice.availability,
                "reason": data["reason"],
                "version": choice.version,
            },
        )
        return Response(
            {"id": str(choice.pk), "availability": choice.availability, "version": choice.version}
        )
