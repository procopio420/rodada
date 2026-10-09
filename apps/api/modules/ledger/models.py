import uuid

from django.db import models

from modules.access.models import StaffMember
from modules.ordering.models import OrderItem, Tab


class Charge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tab = models.ForeignKey(Tab, on_delete=models.PROTECT, related_name="charges")
    order_item = models.OneToOneField(OrderItem, on_delete=models.PROTECT, related_name="charge")
    amount_cents = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class AdjustmentKind(models.TextChoices):
    ITEM_DISCOUNT = "ITEM_DISCOUNT", "Item discount"
    TAB_DISCOUNT = "TAB_DISCOUNT", "Tab discount"
    COURTESY = "COURTESY", "Courtesy"
    SERVICE_CHARGE = "SERVICE_CHARGE", "Service charge"
    SERVICE_CHARGE_REDUCTION = "SERVICE_CHARGE_REDUCTION", "Service reduction"
    REVERSAL = "REVERSAL", "Reversal"
    ORDER_ITEM_CANCELLATION = "ORDER_ITEM_CANCELLATION", "Order item cancellation"
    COURTESY_REPLACEMENT = "COURTESY_REPLACEMENT", "Courtesy replacement"


class LedgerAdjustment(models.Model):
    """An immutable financial fact which compensates, but never edits, a charge."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tab = models.ForeignKey(Tab, on_delete=models.PROTECT, related_name="ledger_adjustments")
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.PROTECT,
        related_name="ledger_adjustments",
        null=True,
        blank=True,
    )
    scope = models.CharField(
        max_length=8, default="CHARGE", choices=[("CHARGE", "Charge"), ("TAB", "Tab")]
    )
    calculation_type = models.CharField(max_length=12, default="DERIVED")
    requested_value = models.PositiveIntegerField(default=0)
    basis_cents = models.PositiveIntegerField(default=0)
    reason_text = models.CharField(max_length=240, blank=True)
    request_fingerprint = models.CharField(max_length=64, blank=True)
    policy_snapshot = models.JSONField(default=dict)
    response = models.JSONField(default=dict)
    approved_by = models.ForeignKey(
        StaffMember,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="pricing_approved",
    )
    reverses = models.OneToOneField(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="reversal"
    )
    kind = models.CharField(max_length=40, choices=AdjustmentKind.choices)
    # Adjustments are signed minor-unit facts. A cancellation is negative and
    # offsets the original positive Charge without destroying either record.
    amount_cents = models.IntegerField()
    idempotency_key = models.CharField(max_length=120)
    reason_code = models.CharField(max_length=80)
    created_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="ledger_adjustments_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("tab", "idempotency_key"),
                name="ledger_adjustment_tab_key_unique",
            ),
            models.UniqueConstraint(
                fields=("order_item", "kind"),
                condition=models.Q(kind__in=["ORDER_ITEM_CANCELLATION", "COURTESY_REPLACEMENT"]),
                name="ledger_adjustment_item_kind_unique",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        kind__in=[
                            "ITEM_DISCOUNT",
                            "TAB_DISCOUNT",
                            "COURTESY",
                            "SERVICE_CHARGE_REDUCTION",
                        ],
                        amount_cents__lte=0,
                    )
                    | models.Q(kind="SERVICE_CHARGE", amount_cents__gte=0)
                    | models.Q(kind="REVERSAL", reverses__isnull=False)
                    | models.Q(
                        kind=AdjustmentKind.ORDER_ITEM_CANCELLATION,
                        amount_cents__lt=0,
                    )
                    | models.Q(
                        kind=AdjustmentKind.COURTESY_REPLACEMENT,
                        amount_cents__lt=0,
                    )
                ),
                name="ledger_adjustment_negative_supported_kind",
            ),
        ]
        indexes = [
            models.Index(fields=("tab", "created_at"), name="ledger_adjustment_tab_time_idx"),
        ]


class PaymentMethod(models.TextChoices):
    TAP_TO_PAY = "TAP_TO_PAY", "Tap to pay"
    CARD_ONLINE = "CARD_ONLINE", "Card online"
    CASH = "CASH", "Cash"
    EXTERNAL_TERMINAL = "EXTERNAL_TERMINAL", "External terminal"
    CARD = "CARD", "Card"
    PIX = "PIX", "Pix"
    OTHER = "OTHER", "Other"


class PaymentStatus(models.TextChoices):
    CREATED = "CREATED", "Created"
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    AUTHORIZED = "AUTHORIZED", "Authorized"
    CONFIRMATION_PENDING = "CONFIRMATION_PENDING", "Confirmation pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    EXPIRED = "EXPIRED", "Expired"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED", "Partially refunded"
    REFUNDED = "REFUNDED", "Refunded"

    @classmethod
    def confirmed_money_values(cls):
        return (cls.CONFIRMED, cls.PARTIALLY_REFUNDED, cls.REFUNDED)


class RefundStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    FAILED = "FAILED", "Failed"


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tab = models.ForeignKey(Tab, on_delete=models.PROTECT, related_name="payments")
    amount_cents = models.PositiveIntegerField()
    method = models.CharField(max_length=24, choices=PaymentMethod.choices)
    idempotency_key = models.CharField(max_length=120)
    currency = models.CharField(max_length=3, default="BRL")
    provider = models.CharField(max_length=80, blank=True)
    provider_payment_id = models.CharField(max_length=160, blank=True)
    status = models.CharField(
        max_length=24, choices=PaymentStatus.choices, default=PaymentStatus.CONFIRMED
    )
    tip_amount_cents = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    received_by = models.ForeignKey(
        StaffMember, on_delete=models.PROTECT, related_name="payments_received"
    )
    received_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("tab", "idempotency_key"), name="ledger_payment_tab_key_unique"
            ),
            models.UniqueConstraint(
                fields=("provider", "provider_payment_id"),
                condition=~models.Q(provider_payment_id=""),
                name="ledger_provider_reference_unique",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(status__in=PaymentStatus.confirmed_money_values())
                    | models.Q(confirmed_at__isnull=False)
                ),
                name="ledger_confirmed_payment_has_timestamp",
            ),
        ]


class Refund(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refunds")
    amount_cents = models.PositiveIntegerField()
    idempotency_key = models.CharField(max_length=120)
    provider_refund_id = models.CharField(max_length=160, blank=True)
    status = models.CharField(
        max_length=16, choices=RefundStatus.choices, default=RefundStatus.CONFIRMED
    )
    reason = models.CharField(max_length=240, blank=True)
    created_by = models.ForeignKey(
        StaffMember, on_delete=models.PROTECT, related_name="refunds_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("payment", "idempotency_key"),
                name="ledger_refund_payment_key_unique",
            )
        ]


class AdjustmentAllocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    adjustment = models.ForeignKey(
        LedgerAdjustment, on_delete=models.PROTECT, related_name="allocations"
    )
    charge = models.ForeignKey(Charge, on_delete=models.PROTECT, related_name="pricing_allocations")
    amount_cents = models.IntegerField()
    basis_cents = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("adjustment", "charge"), name="pricing_allocation_charge_unique"
            )
        ]


class PricingPolicy(models.Model):
    venue = models.OneToOneField("venue.Venue", on_delete=models.PROTECT, primary_key=True)
    version = models.PositiveIntegerField(default=1)
    service_enabled = models.BooleanField(default=False)
    service_basis_points = models.PositiveIntegerField(default=0)
    service_max_basis_points = models.PositiveIntegerField(default=10000)
    service_opt_out = models.BooleanField(default=False)
    service_removal_requires_manager = models.BooleanField(default=True)
    service_treatment = models.CharField(
        max_length=16,
        default="PASS_THROUGH",
        choices=[("REVENUE", "Revenue"), ("PASS_THROUGH", "Pass through")],
    )
    service_refundable = models.BooleanField(default=True)
    staff_discount_basis_points = models.PositiveIntegerField(default=0)
    cashier_discount_basis_points = models.PositiveIntegerField(default=1000)
    maximum_discount_basis_points = models.PositiveIntegerField(default=10000)
    allow_post_payment = models.BooleanField(default=False)


class PricingApproval(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tab = models.ForeignKey(Tab, on_delete=models.PROTECT)
    requested_by = models.ForeignKey("access.StaffSession", on_delete=models.PROTECT)
    idempotency_key = models.CharField(max_length=120)
    request_fingerprint = models.CharField(max_length=64)
    command = models.JSONField()
    preview = models.JSONField()
    adjustment = models.OneToOneField(LedgerAdjustment, null=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("tab", "idempotency_key"), name="pricing_approval_key_unique"
            )
        ]
