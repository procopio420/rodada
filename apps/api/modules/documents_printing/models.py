# ruff: noqa: RUF012
# Django/DRF class-level configuration follows the framework contract.
"""Derived documents and durable delivery; never financial or fulfillment authority."""

import uuid

from django.core.exceptions import ValidationError
from django.db import models


class ImmutableDocumentQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Receipt snapshots are immutable.")

    def delete(self):
        raise ValidationError("Receipt snapshots are immutable.")


class ReceiptDocument(models.Model):
    objects = ImmutableDocumentQuerySet.as_manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey("venue.Venue", on_delete=models.PROTECT)
    tab = models.ForeignKey("ordering.Tab", on_delete=models.PROTECT)
    kind = models.CharField(max_length=32)
    station = models.CharField(max_length=16, blank=True)
    source_id = models.UUIDField()
    source_version = models.CharField(max_length=64)
    template_version = models.PositiveIntegerField(default=1)
    snapshot = models.JSONField()
    snapshot_hash = models.CharField(max_length=64)
    created_by = models.ForeignKey("access.StaffMember", on_delete=models.PROTECT, null=True)
    created_guest_session = models.ForeignKey(
        "guest_access.GuestSession", on_delete=models.PROTECT, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("venue", "kind", "source_id", "station", "source_version"),
                name="printing_document_source_unique",
            )
        ]

    def delete(self, *args, **kwargs):
        raise ValidationError("Receipt snapshots are immutable.")

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Receipt snapshots are immutable.")
        return super().save(*args, **kwargs)


class PrinterEndpoint(models.Model):
    class Adapter(models.TextChoices):
        BROWSER = "BROWSER"
        FILE = "FILE"
        NETWORK = "NETWORK"
        SPOOL = "SPOOL"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey("venue.Venue", on_delete=models.PROTECT)
    label = models.CharField(max_length=120)
    adapter = models.CharField(max_length=16, choices=Adapter.choices)
    connection_ref = models.SlugField(max_length=80, blank=True)
    width_mm = models.PositiveSmallIntegerField(default=80)
    cut_supported = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    health = models.CharField(max_length=16, default="UNKNOWN")
    health_at = models.DateTimeField(null=True)
    bridge_seen_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(width_mm__in=(58, 80)), name="printing_width_supported"
            )
        ]


class StationPrinterBinding(models.Model):
    endpoint = models.ForeignKey(PrinterEndpoint, on_delete=models.PROTECT, related_name="bindings")
    station = models.CharField(max_length=16, choices=[("BAR", "Bar"), ("KITCHEN", "Kitchen")])
    enabled = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("endpoint", "station"), name="printing_binding_unique")
        ]


class PrintJob(models.Model):
    class State(models.TextChoices):
        QUEUED = "QUEUED"
        SENDING = "SENDING"
        FAILED_RETRYABLE = "FAILED_RETRYABLE"
        FAILED_FINAL = "FAILED_FINAL"
        DELIVERY_UNCERTAIN = "DELIVERY_UNCERTAIN"
        SPOOL_ACCEPTED = "SPOOL_ACCEPTED"
        OUTPUT_READY = "OUTPUT_READY"
        PRINTED = "PRINTED"
        CANCELLED = "CANCELLED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(ReceiptDocument, on_delete=models.PROTECT, related_name="jobs")
    endpoint = models.ForeignKey(PrinterEndpoint, on_delete=models.PROTECT)
    idempotency_key = models.CharField(max_length=120)
    initial_production_key = models.UUIDField(null=True, unique=True)
    state = models.CharField(max_length=32, choices=State.choices, default=State.QUEUED)
    reprint_of = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True)
    requested_by = models.ForeignKey("access.StaffMember", on_delete=models.PROTECT)
    reason = models.CharField(max_length=240, blank=True)
    attempt_count = models.PositiveIntegerField(default=0)
    available_at = models.DateTimeField()
    lease_until = models.DateTimeField(null=True)
    attempt_token = models.UUIDField(null=True)
    last_error = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("endpoint", "idempotency_key"), name="printing_job_key_unique"
            ),
            models.UniqueConstraint(
                fields=("document", "endpoint"),
                condition=models.Q(reprint_of__isnull=True),
                name="printing_initial_job_unique",
            ),
        ]
        indexes = [models.Index(fields=("state", "available_at"), name="printing_due_idx")]


class PrintAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(PrintJob, on_delete=models.PROTECT, related_name="attempts")
    token = models.UUIDField(unique=True)
    number = models.PositiveIntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True)
    outcome = models.CharField(max_length=32, blank=True)
    detail = models.CharField(max_length=240, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("job", "number"), name="printing_attempt_number_unique")
        ]


class ReceiptAccessToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(ReceiptDocument, on_delete=models.PROTECT)
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey("access.StaffMember", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
