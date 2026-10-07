import uuid

from django.db import models
from django.db.models import Q

from modules.access.models import StaffMember
from modules.catalog.models import Product
from modules.venue.models import Venue


class TabState(models.TextChoices):
    OPEN = "OPEN", "Open"
    REQUIRES_ACTION = "REQUIRES_ACTION", "Requires action"
    SETTLING = "SETTLING", "Settling"
    CLOSED = "CLOSED", "Closed"
    CANCELLED = "CANCELLED", "Cancelled"


class OrderSource(models.TextChoices):
    STAFF = "STAFF", "Staff"
    CASHIER = "CASHIER", "Cashier"
    GUEST = "GUEST", "Guest"


class OrderStatus(models.TextChoices):
    CONFIRMED = "CONFIRMED", "Confirmed"
    CANCELLED = "CANCELLED", "Cancelled"


class OrderItemState(models.TextChoices):
    NEW = "NEW", "New"
    ACCEPTED = "ACCEPTED", "Accepted"
    PREPARING = "PREPARING", "Preparing"
    READY = "READY", "Ready"
    PICKED_UP = "PICKED_UP", "Picked up"
    DELIVERED = "DELIVERED", "Delivered"
    CANCELLED = "CANCELLED", "Cancelled"


class Tab(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="tabs")
    display_label = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=24, choices=TabState.choices, default=TabState.OPEN)
    version = models.PositiveIntegerField(default=1)
    opened_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="tabs_opened",
        null=True,
        blank=True,
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-opened_at", "id")
        indexes = [
            models.Index(fields=("venue", "state", "opened_at"), name="ordering_tab_v_state_idx"),
        ]


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tab = models.ForeignKey(Tab, on_delete=models.PROTECT, related_name="orders")
    source = models.CharField(max_length=16, choices=OrderSource.choices)
    status = models.CharField(
        max_length=16,
        choices=OrderStatus.choices,
        default=OrderStatus.CONFIRMED,
    )
    confirmed_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="orders_confirmed",
        null=True,
        blank=True,
    )
    confirmed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("confirmed_at", "id")
        indexes = [
            models.Index(fields=("tab", "confirmed_at"), name="ordering_ord_tab_time_idx"),
        ]


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    product_name_snapshot = models.CharField(max_length=160)
    unit_price_cents = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()
    state = models.CharField(
        max_length=16,
        choices=OrderItemState.choices,
        default=OrderItemState.NEW,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    preparing_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("created_at", "id")
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="ordering_item_quantity_positive",
            ),
        ]
        indexes = [
            models.Index(fields=("order", "state"), name="ordering_item_ord_state_idx"),
            models.Index(fields=("product", "created_at"), name="ordering_item_product_idx"),
        ]

    @property
    def line_total_cents(self) -> int:
        return self.unit_price_cents * self.quantity
