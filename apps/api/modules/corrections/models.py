import uuid

from django.db import models
from django.db.models import Q

from modules.access.models import StaffMember
from modules.ledger.models import LedgerAdjustment
from modules.ledger.models import Refund
from modules.ordering.models import OrderItem
from modules.venue.models import Venue


class CorrectionKind(models.TextChoices):
    CANCEL_ITEM = "CANCEL_ITEM", "Cancel item"
    CUSTOMER_CHANGED_MIND = "CUSTOMER_CHANGED_MIND", "Customer changed mind"
    WRONG_ITEM_ENTERED = "WRONG_ITEM_ENTERED", "Wrong item entered"
    STATION_MISTAKE = "STATION_MISTAKE", "Station mistake"
    CUSTOMER_REJECTED = "CUSTOMER_REJECTED", "Customer rejected"
    REMAKE = "REMAKE", "Remake"
    REPLACEMENT = "REPLACEMENT", "Replacement"
    COMPLAINT = "COMPLAINT", "Complaint"
    OTHER_EXCEPTION = "OTHER_EXCEPTION", "Other exception"


class CorrectionStatus(models.TextChoices):
    REQUESTED = "REQUESTED", "Requested"
    APPLIED = "APPLIED", "Applied"
    REJECTED = "REJECTED", "Rejected"


class FinancialDisposition(models.TextChoices):
    NONE = "NONE", "None"
    REVERSE_OPEN_RESPONSIBILITY = "REVERSE_OPEN_RESPONSIBILITY", "Reverse open responsibility"
    COURTESY_REPLACEMENT = "COURTESY_REPLACEMENT", "Courtesy replacement"
    REFUND_REQUIRED = "REFUND_REQUIRED", "Refund required"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED", "Manual review required"


class WasteKind(models.TextChoices):
    PREPARED_NOT_SERVED = "PREPARED_NOT_SERVED", "Prepared not served"
    REMAKE_DISCARDED = "REMAKE_DISCARDED", "Remake discarded"
    SPOILAGE = "SPOILAGE", "Spoilage"
    OTHER = "OTHER", "Other"


class OrderCorrection(models.Model):
    """Append-only account of a post-confirmation operational mistake."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="order_corrections")
    original_order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.PROTECT,
        related_name="corrections",
    )
    kind = models.CharField(max_length=32, choices=CorrectionKind.choices)
    stage_at_request = models.CharField(max_length=16)
    status = models.CharField(
        max_length=16,
        choices=CorrectionStatus.choices,
        default=CorrectionStatus.REQUESTED,
    )
    reason_code = models.CharField(max_length=80)
    reason_text = models.CharField(max_length=400, blank=True)
    financial_disposition = models.CharField(
        max_length=32,
        choices=FinancialDisposition.choices,
        default=FinancialDisposition.NONE,
    )
    idempotency_key = models.CharField(max_length=120)
    request_fingerprint = models.CharField(max_length=64)
    requested_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="order_corrections_requested",
    )
    approved_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="order_corrections_approved",
        null=True,
        blank=True,
    )
    # A remake/replacement is always another immutable OrderItem, never a
    # mutation or reset of the original item's snapshot/history.
    replacement_order_item = models.OneToOneField(
        OrderItem,
        on_delete=models.PROTECT,
        related_name="replacement_correction",
        null=True,
        blank=True,
    )
    financial_adjustment = models.OneToOneField(
        LedgerAdjustment,
        on_delete=models.PROTECT,
        related_name="correction",
        null=True,
        blank=True,
    )
    refund = models.OneToOneField(
        Refund,
        on_delete=models.PROTECT,
        related_name="settled_correction",
        null=True,
        blank=True,
    )
    # When a correction has already changed the append-only responsibility but
    # confirmed money now exceeds it, this is the exact canonical refund still
    # required.  It prevents a UI or retry from guessing a partial amount.
    refund_required_cents = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("created_at", "id")
        indexes = [
            models.Index(
                fields=("venue", "original_order_item", "created_at"),
                name="correction_origin_time_idx",
            ),
            models.Index(
                fields=("replacement_order_item",),
                name="correction_replacement_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("original_order_item", "idempotency_key"),
                condition=~Q(idempotency_key=""),
                name="correction_item_idempotency_unique",
            ),
        ]


class WasteMarker(models.Model):
    """Operational evidence only; it never changes inventory or ledger state."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="waste_markers")
    order_item = models.ForeignKey(OrderItem, on_delete=models.PROTECT, related_name="waste_markers")
    correction = models.ForeignKey(
        OrderCorrection,
        on_delete=models.PROTECT,
        related_name="waste_markers",
        null=True,
        blank=True,
    )
    kind = models.CharField(max_length=32, choices=WasteKind.choices)
    quantity = models.PositiveIntegerField()
    reason = models.CharField(max_length=400, blank=True)
    created_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="waste_markers_created",
    )
    occurred_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("occurred_at", "id")
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="correction_waste_quantity_positive",
            ),
        ]
        indexes = [
            models.Index(
                fields=("venue", "order_item", "occurred_at"),
                name="correction_waste_item_time_idx",
            ),
        ]
