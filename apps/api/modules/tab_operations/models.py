import uuid
from django.db import models
from django.db.models import Q, F


class ServicePoint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey("venue.Venue", on_delete=models.PROTECT)
    label = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("venue", "label"), name="tabop_point_label_unique")]


class TabOperation(models.Model):
    """Durable command result, also covering non-financial operations."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_tab = models.ForeignKey("ordering.Tab", on_delete=models.PROTECT, related_name="operations")
    idempotency_key = models.CharField(max_length=120)
    request_fingerprint = models.CharField(max_length=64)
    kind = models.CharField(max_length=24)
    created_by = models.ForeignKey("access.StaffMember", on_delete=models.PROTECT)
    response = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("source_tab", "idempotency_key"), name="tabop_command_key_unique")]


class TabTransfer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operation = models.OneToOneField(TabOperation, on_delete=models.PROTECT, related_name="transfer")
    venue = models.ForeignKey("venue.Venue", on_delete=models.PROTECT)
    source_tab = models.ForeignKey("ordering.Tab", on_delete=models.PROTECT, related_name="outgoing_transfers")
    destination_tab = models.ForeignKey("ordering.Tab", on_delete=models.PROTECT, related_name="incoming_transfers")
    kind = models.CharField(max_length=16, choices=[(v, v) for v in ("SPLIT", "MOVE_ITEMS", "MERGE")])
    status = models.CharField(max_length=16, default="COMMITTED", choices=[("COMMITTED", "COMMITTED")])
    reason = models.CharField(max_length=240, blank=True)
    source_version = models.PositiveIntegerField()
    destination_version = models.PositiveIntegerField()
    committed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=~Q(source_tab=F("destination_tab")), name="tabop_distinct_tabs")]
        indexes = [models.Index(fields=("venue", "committed_at"), name="tabop_venue_time_idx")]


class TabTransferLine(models.Model):
    """One immutable pair: -amount on source, +amount on destination."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transfer = models.ForeignKey(TabTransfer, on_delete=models.PROTECT, related_name="lines")
    source_charge = models.ForeignKey("ledger.Charge", on_delete=models.PROTECT, related_name="transfer_lines")
    amount_cents = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount_cents__gt=0), name="tabop_line_positive"),
            models.UniqueConstraint(fields=("transfer", "source_charge"), name="tabop_transfer_charge_unique"),
        ]
