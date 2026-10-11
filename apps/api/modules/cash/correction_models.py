"""Two-person approvals for post-close cash corrections.

Requests are financial proposals, not drawer movements. A request cannot affect
the ledger until a different authorized operator explicitly approves it.
"""
import uuid

from django.db import models
from django.db.models import Q


class CashCorrectionRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shift = models.ForeignKey("cash.CashShift", on_delete=models.PROTECT, related_name="correction_requests")
    requested_by = models.ForeignKey("access.StaffMember", on_delete=models.PROTECT, related_name="cash_corrections_requested")
    requested_at = models.DateTimeField()
    amount_cents = models.IntegerField()
    reason = models.CharField(max_length=240)
    idempotency_key = models.CharField(max_length=120)
    correction_of = models.ForeignKey(
        "cash.CashMovement", on_delete=models.PROTECT, null=True, blank=True, related_name="correction_requests"
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    version = models.PositiveIntegerField(default=1)
    decided_by = models.ForeignKey(
        "access.StaffMember", on_delete=models.PROTECT, null=True, blank=True, related_name="cash_corrections_decided"
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_reason = models.CharField(max_length=240, blank=True)
    movement = models.OneToOneField(
        "cash.CashMovement", on_delete=models.PROTECT, null=True, blank=True, related_name="approved_request"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("shift", "idempotency_key"), name="cash_correction_request_unique"),
            models.CheckConstraint(
                condition=Q(amount_cents__gt=0) | Q(amount_cents__lt=0),
                name="cash_correction_request_nonzero",
            ),
        ]
        indexes = [
            models.Index(fields=("shift", "status"), name="cash_correction_shift_idx"),
        ]
