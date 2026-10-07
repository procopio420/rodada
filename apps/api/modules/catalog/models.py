import re
import unicodedata
import uuid

from django.db import models

from modules.access.models import StaffMember
from modules.venue.models import Venue


def normalize_product_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
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
        super().save(*args, **kwargs)
        if creating:
            ProductAvailability.objects.get_or_create(product=self)

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
