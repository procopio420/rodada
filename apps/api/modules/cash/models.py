import uuid

from django.db import models
from django.db.models import Q

from modules.access.models import DeviceRegistration, StaffMember, StaffSession
from modules.venue.models import Venue


class CashPoint(models.Model):
    """A physical drawer or other place where cash is held."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="cash_points")
    label = models.CharField(max_length=120)
    active = models.BooleanField(default=True)
    device = models.ForeignKey(
        DeviceRegistration,
        on_delete=models.SET_NULL,
        related_name="cash_points",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("venue", "label"),
                name="cash_point_venue_label_unique",
            )
        ]
        indexes = [models.Index(fields=("venue", "active"), name="cash_point_venue_active_idx")]

    def __str__(self) -> str:
        return self.label


class CashShiftStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    COUNTING = "COUNTING", "Counting"
    CLOSED = "CLOSED", "Closed"


class CashReviewStatus(models.TextChoices):
    NOT_REQUIRED = "NOT_REQUIRED", "Not required"
    PENDING = "PENDING", "Pending"
    REVIEWED = "REVIEWED", "Reviewed"


class CashShift(models.Model):
    """One operational custody period for a CashPoint.

    Closing observations are immutable snapshots.  Later corrections are facts
    in CashMovement and never rewrite these fields.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="cash_shifts")
    cash_point = models.ForeignKey(CashPoint, on_delete=models.PROTECT, related_name="shifts")
    business_date = models.DateField()
    status = models.CharField(
        max_length=12, choices=CashShiftStatus.choices, default=CashShiftStatus.OPEN
    )
    opened_by = models.ForeignKey(
        StaffMember, on_delete=models.PROTECT, related_name="cash_shifts_opened"
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    opening_float_cents = models.PositiveIntegerField(default=0)
    opening_idempotency_key = models.CharField(max_length=120)
    closed_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="cash_shifts_closed",
        null=True,
        blank=True,
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    counted_amount_cents = models.PositiveIntegerField(null=True, blank=True)
    expected_amount_cents_snapshot = models.IntegerField(null=True, blank=True)
    discrepancy_cents = models.IntegerField(null=True, blank=True)
    review_status = models.CharField(
        max_length=16,
        choices=CashReviewStatus.choices,
        default=CashReviewStatus.NOT_REQUIRED,
    )
    reviewed_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="cash_shifts_reviewed",
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_reason = models.CharField(max_length=240, blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("cash_point",),
                condition=Q(status__in=(CashShiftStatus.OPEN, CashShiftStatus.COUNTING)),
                name="cash_one_active_shift_per_point",
            ),
            models.UniqueConstraint(
                fields=("cash_point", "opening_idempotency_key"),
                name="cash_shift_opening_idempotency_unique",
            ),
        ]
        indexes = [
            models.Index(fields=("venue", "business_date"), name="cash_shift_venue_date_idx"),
            models.Index(fields=("cash_point", "status"), name="cash_shift_point_status_idx"),
        ]


class CashMovementKind(models.TextChoices):
    OPENING_FLOAT = "OPENING_FLOAT", "Opening float"
    CASH_PAYMENT = "CASH_PAYMENT", "Cash payment"
    CASH_REFUND = "CASH_REFUND", "Cash refund"
    SUPPLY = "SUPPLY", "Supply"
    WITHDRAWAL = "WITHDRAWAL", "Withdrawal"
    CORRECTION = "CORRECTION", "Correction"


class CashMovement(models.Model):
    """Append-only physical drawer fact. amount_cents is signed."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shift = models.ForeignKey(CashShift, on_delete=models.PROTECT, related_name="movements")
    kind = models.CharField(max_length=20, choices=CashMovementKind.choices)
    amount_cents = models.IntegerField()
    payment = models.OneToOneField(
        "ledger.Payment",
        on_delete=models.PROTECT,
        related_name="cash_movement",
        null=True,
        blank=True,
    )
    refund = models.OneToOneField(
        "ledger.Refund",
        on_delete=models.PROTECT,
        related_name="cash_movement",
        null=True,
        blank=True,
    )
    actor = models.ForeignKey(
        StaffMember, on_delete=models.PROTECT, related_name="cash_movements"
    )
    actor_session = models.ForeignKey(
        StaffSession,
        on_delete=models.PROTECT,
        related_name="cash_movements",
        null=True,
        blank=True,
    )
    device = models.ForeignKey(
        DeviceRegistration,
        on_delete=models.PROTECT,
        related_name="cash_movements",
        null=True,
        blank=True,
    )
    reason = models.CharField(max_length=240, blank=True)
    occurred_at = models.DateTimeField()
    recorded_at = models.DateTimeField(auto_now_add=True)
    idempotency_key = models.CharField(max_length=120)
    correction_of = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="corrections",
        null=True,
        blank=True,
    )
    is_post_close_correction = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_cents__gt=0) | Q(amount_cents__lt=0),
                name="cash_movement_amount_nonzero",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        kind__in=(
                            CashMovementKind.OPENING_FLOAT,
                            CashMovementKind.CASH_PAYMENT,
                            CashMovementKind.SUPPLY,
                        ),
                        amount_cents__gt=0,
                    )
                    | Q(
                        kind__in=(CashMovementKind.CASH_REFUND, CashMovementKind.WITHDRAWAL),
                        amount_cents__lt=0,
                    )
                    | Q(kind=CashMovementKind.CORRECTION)
                ),
                name="cash_movement_kind_direction",
            ),
            models.UniqueConstraint(
                fields=("shift", "idempotency_key"),
                name="cash_movement_shift_idempotency_unique",
            ),
        ]
        indexes = [
            models.Index(fields=("shift", "recorded_at"), name="cash_move_shift_recorded_idx"),
            models.Index(fields=("shift", "kind"), name="cash_move_shift_kind_idx"),
        ]


class CashTenderDetail(models.Model):
    """Tender/change observation for a confirmed cash Payment.

    The payment amount is the net drawer effect. Tender and change are never
    added independently to expected cash.
    """

    payment = models.OneToOneField(
        "ledger.Payment", on_delete=models.PROTECT, related_name="cash_tender_detail"
    )
    shift = models.ForeignKey(CashShift, on_delete=models.PROTECT, related_name="cash_tenders")
    amount_due_cents = models.PositiveIntegerField()
    amount_tendered_cents = models.PositiveIntegerField()
    change_given_cents = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_tendered_cents__gte=models.F("change_given_cents")),
                name="cash_tender_change_not_exceed_tender",
            )
        ]
