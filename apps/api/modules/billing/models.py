import uuid

from django.db import models
from django.db.models import Q

from modules.access.models import StaffMember
from modules.ordering.models import OrderItem, Tab
from modules.venue.models import Venue


class ChargeKind(models.TextChoices):
    CONSUMPTION = "CONSUMPTION", "Consumption"


class PaymentMethod(models.TextChoices):
    TAP_TO_PAY = "TAP_TO_PAY", "Tap to Pay"
    PIX = "PIX", "Pix"
    CARD_ONLINE = "CARD_ONLINE", "Card online"
    CASH = "CASH", "Cash"
    EXTERNAL_TERMINAL = "EXTERNAL_TERMINAL", "External terminal"
    OTHER = "OTHER", "Other"


class PaymentStatus(models.TextChoices):
    CREATED = "CREATED", "Created"
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    AUTHORIZED = "AUTHORIZED", "Authorized"
    CONFIRMATION_PENDING = "CONFIRMATION_PENDING", "Confirmation pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED", "Partially refunded"
    REFUNDED = "REFUNDED", "Refunded"


class AdjustmentKind(models.TextChoices):
    ITEM_DISCOUNT = "ITEM_DISCOUNT", "Item discount"
    TAB_DISCOUNT = "TAB_DISCOUNT", "Tab discount"
    COURTESY = "COURTESY", "Courtesy"
    SERVICE_CHARGE = "SERVICE_CHARGE", "Service charge"
    SERVICE_CHARGE_REDUCTION = "SERVICE_CHARGE_REDUCTION", "Service charge reduction"
    CORRECTION = "CORRECTION", "Correction"
    REVERSAL = "REVERSAL", "Reversal"


class AdjustmentScope(models.TextChoices):
    CHARGE = "CHARGE", "Charge"
    TAB = "TAB", "Tab"


class AdjustmentCalculationType(models.TextChoices):
    PERCENTAGE = "PERCENTAGE", "Percentage"
    FIXED = "FIXED", "Fixed"
    DERIVED = "DERIVED", "Derived"


class Charge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="charges")
    tab = models.ForeignKey(Tab, on_delete=models.PROTECT, related_name="charges")
    order_item = models.OneToOneField(
        OrderItem,
        on_delete=models.PROTECT,
        related_name="charge",
    )
    kind = models.CharField(
        max_length=20,
        choices=ChargeKind.choices,
        default=ChargeKind.CONSUMPTION,
    )
    amount_cents = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_cents__gte=0),
                name="billing_charge_amount_nonnegative",
            ),
        ]
        indexes = [
            models.Index(fields=("tab", "created_at"), name="billing_charge_tab_time_idx"),
        ]


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="payments")
    tab = models.ForeignKey(Tab, on_delete=models.PROTECT, related_name="payments")
    amount_cents = models.PositiveIntegerField()
    method = models.CharField(max_length=24, choices=PaymentMethod.choices)
    status = models.CharField(
        max_length=24,
        choices=PaymentStatus.choices,
        default=PaymentStatus.CREATED,
    )
    idempotency_key = models.CharField(max_length=120)
    provider = models.CharField(max_length=64, blank=True)
    external_reference = models.CharField(max_length=160, blank=True)
    created_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="payments_created",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_cents__gt=0),
                name="billing_payment_amount_positive",
            ),
            models.UniqueConstraint(
                fields=("venue", "idempotency_key"),
                name="billing_unique_payment_idempotency",
            ),
        ]
        indexes = [
            models.Index(fields=("tab", "status", "created_at"), name="billing_pay_tab_status_idx"),
        ]


class Adjustment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="adjustments")
    tab = models.ForeignKey(Tab, on_delete=models.PROTECT, related_name="adjustments")
    kind = models.CharField(max_length=32, choices=AdjustmentKind.choices)
    scope = models.CharField(max_length=16, choices=AdjustmentScope.choices)
    source_charge = models.ForeignKey(
        Charge,
        on_delete=models.PROTECT,
        related_name="adjustments",
        null=True,
        blank=True,
    )
    calculation_type = models.CharField(
        max_length=16,
        choices=AdjustmentCalculationType.choices,
    )
    requested_value = models.IntegerField(null=True, blank=True)
    effect_cents = models.IntegerField()
    reason_code = models.CharField(max_length=64, blank=True)
    reason_text = models.CharField(max_length=240, blank=True)
    created_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="adjustments_created",
        null=True,
        blank=True,
    )
    approved_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="adjustments_approved",
        null=True,
        blank=True,
    )
    supersedes_adjustment = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="superseding_adjustments",
        null=True,
        blank=True,
    )
    idempotency_key = models.CharField(max_length=120)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("venue", "idempotency_key"),
                name="billing_unique_adjustment_idempotency",
            ),
        ]
        indexes = [
            models.Index(fields=("tab", "created_at"), name="billing_adj_tab_time_idx"),
            models.Index(fields=("source_charge", "created_at"), name="billing_adj_charge_idx"),
        ]
