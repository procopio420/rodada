from django.db import models
import hashlib


class CanonicalItem(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    icon_key = models.CharField(max_length=64, blank=True)
    icon_status = models.CharField(max_length=16, default="PENDING")
    icon_attempts = models.PositiveSmallIntegerField(default=0)
    icon_generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def ensure_fallback(self):
        if not self.icon_key:
            self.icon_key = hashlib.sha256(f"{self.name}|{self.description}".encode()).hexdigest()[:24]


class Product(models.Model):
    class Station(models.TextChoices):
        BAR = "BAR", "Bar"
        KITCHEN = "KITCHEN", "Cozinha"
        NONE = "NONE", "Sem preparo"

    venue = models.ForeignKey("pos.Venue", on_delete=models.PROTECT, related_name="products")
    canonical_item = models.ForeignKey(CanonicalItem, null=True, blank=True, on_delete=models.PROTECT, related_name="menu_products")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    available = models.BooleanField(default=True)
    current_price_cents = models.PositiveIntegerField()
    fulfillment_station = models.CharField(max_length=16, choices=Station.choices, default=Station.BAR)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(current_price_cents__gte=0), name="product_price_nonnegative")]
        ordering = ["name"]
