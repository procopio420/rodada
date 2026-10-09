import re
import unicodedata
import uuid

from django.db import models, transaction

from modules.access.models import StaffMember
from modules.venue.models import Venue


def normalize_product_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    normalized = "".join(c for c in unicodedata.normalize("NFKD", normalized) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", normalized)


class FulfillmentStation(models.TextChoices):
    BAR = "BAR", "Bar"
    KITCHEN = "KITCHEN", "Kitchen"


class AvailabilityState(models.TextChoices):
    AVAILABLE = "AVAILABLE", "Available"
    UNAVAILABLE = "UNAVAILABLE", "Unavailable"


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=160)
    normalized_name = models.CharField(max_length=180, editable=False)
    description = models.CharField(max_length=600, blank=True)
    category = models.CharField(max_length=100, blank=True)
    price_cents = models.PositiveIntegerField()
    active = models.BooleanField(default=True)
    fulfillment_station = models.CharField(max_length=16, choices=FulfillmentStation.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("venue", "normalized_name"),
                name="catalog_unique_product_name_per_venue",
            ),
        ]
        indexes = [
            models.Index(
                fields=("venue", "active", "fulfillment_station"),
                name="catalog_v_active_station_idx",
            ),
        ]
        ordering = ("name", "id")

    def save(self, *args, **kwargs):
        self.normalized_name = normalize_product_name(self.name)
        creating = self._state.adding
        if kwargs.get("update_fields") and "name" in kwargs["update_fields"]:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"normalized_name"}
        with transaction.atomic():
            super().save(*args, **kwargs)
            if creating:
                ProductAvailability.objects.get_or_create(product=self)
                ProductIcon.objects.get_or_create(product=self)
                from modules.catalog.services import enqueue_icon
                enqueue_icon(product=self)

    def __str__(self) -> str:
        return self.name


class ProductAvailability(models.Model):
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="availability",
    )
    state = models.CharField(
        max_length=16,
        choices=AvailabilityState.choices,
        default=AvailabilityState.AVAILABLE,
    )
    version = models.PositiveIntegerField(default=1)
    changed_at = models.DateTimeField(auto_now=True)
    changed_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="product_availability_changes",
        null=True,
        blank=True,
    )
    reason = models.CharField(max_length=240, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=("state", "changed_at"), name="catalog_avail_state_idx"),
        ]


class ProductIcon(models.Model):
    """Stable product-keyed identity, extended with durable generation and revisions."""
    product = models.OneToOneField(Product, on_delete=models.CASCADE, primary_key=True, related_name="icon")
    source = models.CharField(max_length=24, default="NONE")
    status = models.CharField(max_length=16, default="FAILED")
    published_asset_url = models.URLField(blank=True)
    style_version = models.CharField(max_length=40, default="rodada-icon-v1")
    error_code = models.CharField(max_length=80, default="GENERATOR_NOT_CONFIGURED")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    published_asset = models.CharField(max_length=240, blank=True)
    revision = models.PositiveIntegerField(default=0)

    @property
    def id(self):
        return self.pk


class IconGeneration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    icon = models.ForeignKey(ProductIcon, on_delete=models.CASCADE, related_name="generations")
    fingerprint = models.CharField(max_length=64)
    request_key = models.CharField(max_length=160)
    revision = models.PositiveIntegerField()
    context = models.JSONField()
    prompt = models.TextField()
    style_version = models.CharField(max_length=40)
    provider = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    usage = models.JSONField(default=dict)
    asset = models.CharField(max_length=240, blank=True)
    status = models.CharField(max_length=16, default="PENDING")
    attempts = models.PositiveIntegerField(default=0)
    available_at = models.DateTimeField()
    lease_until = models.DateTimeField(null=True)
    claim_token = models.UUIDField(null=True)
    error = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(StaffMember, on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("icon", "request_key"), name="catalog_icon_request_unique")]
        indexes = [models.Index(fields=("status", "available_at"), name="catalog_icon_jobs_idx")]


class IconGenerationRequest(models.Model):
    icon = models.ForeignKey(ProductIcon, on_delete=models.CASCADE)
    key = models.CharField(max_length=160)
    generation = models.ForeignKey(IconGeneration, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("icon", "key"), name="catalog_icon_alias_unique")]


class ProductVariant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=100)
    price_cents = models.PositiveIntegerField()
    active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    availability = models.CharField(max_length=16, choices=AvailabilityState.choices, default=AvailabilityState.AVAILABLE)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ("sort_order", "id")
        constraints = [models.UniqueConstraint(fields=["product"], condition=models.Q(is_default=True, active=True), name="catalog_one_default_variant")]


class ModifierGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="modifier_groups")
    name = models.CharField(max_length=100)
    selection_mode = models.CharField(max_length=8, choices=[("SINGLE", "Single"), ("MULTI", "Multi")])
    min_selections = models.PositiveIntegerField(default=0)
    max_selections = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(max_selections__gte=models.F("min_selections")) & models.Q(max_selections__gte=1), name="catalog_group_bounds"),
            models.CheckConstraint(condition=models.Q(selection_mode="MULTI") | models.Q(selection_mode="SINGLE", max_selections=1), name="catalog_single_group_max"),
        ]


class ModifierOption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(ModifierGroup, on_delete=models.CASCADE, related_name="options")
    name = models.CharField(max_length=100)
    price_delta_cents = models.PositiveIntegerField(default=0)
    semantic_kind = models.CharField(max_length=8, choices=[("ADD", "Add"), ("REMOVE", "Remove"), ("CHOICE", "Choice")], default="CHOICE")
    active = models.BooleanField(default=True)
    default_selected = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    availability = models.CharField(max_length=16, choices=AvailabilityState.choices, default=AvailabilityState.AVAILABLE)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ("sort_order", "id")


class ProductModifierGroup(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="modifier_links")
    group = models.ForeignKey(ModifierGroup, on_delete=models.CASCADE, related_name="product_links")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "id")
        constraints = [models.UniqueConstraint(fields=["product", "group"], name="catalog_product_group_unique")]
