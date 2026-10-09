import uuid

from django.db import models

from modules.ledger.models import Payment


class PaymentAttemptStatus(models.TextChoices):
    CREATED = "CREATED", "Created"
    PROCESSING = "PROCESSING", "Processing"
    CONFIRMATION_PENDING = "CONFIRMATION_PENDING", "Confirmation pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"


class ProviderEventProcessingStatus(models.TextChoices):
    RECEIVED = "RECEIVED", "Received"
    APPLIED = "APPLIED", "Applied"
    IGNORED = "IGNORED", "Ignored"
    FAILED = "FAILED", "Failed"


class PaymentAttempt(models.Model):
    """One provider interaction, never a source of financial truth by itself."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="provider_attempts")
    idempotency_key = models.CharField(max_length=120)
    provider = models.CharField(max_length=80)
    provider_attempt_id = models.CharField(max_length=160, blank=True)
    status = models.CharField(
        max_length=24, choices=PaymentAttemptStatus.choices, default=PaymentAttemptStatus.CREATED
    )
    error_code = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("started_at", "id")
        constraints = (
            models.UniqueConstraint(
                fields=("payment", "idempotency_key"),
                name="provider_attempt_payment_key_uniq",
            ),
        )
        indexes = (
            models.Index(
                fields=("provider", "provider_attempt_id"), name="provider_attempt_ref_idx"
            ),
            models.Index(fields=("payment", "status"), name="payprov_attempt_stat_idx"),
        )


class ProviderEvent(models.Model):
    """Idempotent inbox evidence for a provider callback; no raw card payload."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=80)
    provider_event_id = models.CharField(max_length=160)
    payload_hash = models.CharField(max_length=64)
    event_type = models.CharField(max_length=100)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="provider_events",
        null=True,
        blank=True,
    )
    attempt = models.ForeignKey(
        PaymentAttempt,
        on_delete=models.PROTECT,
        related_name="provider_events",
        null=True,
        blank=True,
    )
    processing_status = models.CharField(
        max_length=16,
        choices=ProviderEventProcessingStatus.choices,
        default=ProviderEventProcessingStatus.RECEIVED,
    )
    processing_error = models.CharField(max_length=160, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("received_at", "id")
        constraints = (
            models.UniqueConstraint(
                fields=("provider", "provider_event_id"),
                name="provider_event_provider_id_uniq",
            ),
        )
        indexes = (models.Index(fields=("payment", "received_at"), name="payprov_event_time_idx"),)


class MerchantConnection(models.Model):
    """One immutable merchant identity per connection; tokens are AEAD encrypted."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey("venue.Venue", on_delete=models.PROTECT)
    provider = models.CharField(max_length=24)
    merchant_code = models.CharField(max_length=80)
    active = models.BooleanField(default=True)
    simulated = models.BooleanField(default=False)
    capabilities = models.JSONField(default=dict)
    encrypted_credentials = models.TextField(blank=True)
    token_expires_at = models.DateTimeField(null=True)
    scopes = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    disconnected_at = models.DateTimeField(null=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("venue", "provider", "merchant_code"), name="payprov_merchant_venue_unique"
            ),
        )


class DeviceAuthorization(models.Model):
    connection = models.ForeignKey(MerchantConnection, on_delete=models.PROTECT)
    device = models.ForeignKey("access.DeviceRegistration", on_delete=models.PROTECT)
    staff = models.ForeignKey("access.StaffMember", on_delete=models.PROTECT)
    active = models.BooleanField(default=True)
    authorized_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("connection", "device", "staff"), name="payprov_device_operator_unique"
            ),
        )


class OAuthAuthorization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey("venue.Venue", on_delete=models.PROTECT)
    staff = models.ForeignKey("access.StaffMember", on_delete=models.PROTECT)
    state_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True)


class SimulatedTransaction(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.PROTECT)
    status = models.CharField(max_length=24, default="PENDING")
    scenario = models.CharField(max_length=24, default="success")
    lookup_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class ProviderRefundRequest(models.Model):
    refund = models.OneToOneField("ledger.Refund", on_delete=models.PROTECT)
    transaction_id = models.CharField(max_length=160)
    baseline_event_ids = models.JSONField(default=list)
    submitted_at = models.DateTimeField(auto_now_add=True)
