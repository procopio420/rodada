import uuid

from django.db import models

from modules.hospitality.models import Table, TableOccupancy
from modules.ordering.models import Tab


class GuestSession(models.Model):
    """Revocable browser credential scoped to one table visit and one Tab.

    The browser receives the opaque secret once.  Only its SHA-256 digest is
    persisted, so a database read alone cannot be used as a guest credential.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    table = models.ForeignKey(Table, on_delete=models.PROTECT, related_name="guest_sessions")
    occupancy = models.ForeignKey(
        TableOccupancy,
        on_delete=models.PROTECT,
        related_name="guest_sessions",
        null=True,
        blank=True,
    )
    tab = models.ForeignKey(
        Tab,
        on_delete=models.PROTECT,
        related_name="guest_sessions",
        null=True,
        blank=True,
    )
    generation = models.PositiveIntegerField()
    token_digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_reason = models.CharField(max_length=120, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "id")
        indexes = (
            models.Index(fields=("table", "generation"), name="guest_session_table_gen_idx"),
            models.Index(fields=("occupancy", "revoked_at"), name="guest_session_occ_rev_idx"),
            models.Index(fields=("expires_at",), name="guest_session_expiry_idx"),
        )



class CustomerCredential(models.Model):
    """Opt-in self-enrolled credential; never auto-trust a legacy Customer label."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.OneToOneField(
        "house_account.Customer", on_delete=models.PROTECT, related_name="guest_credential"
    )
    username = models.CharField(max_length=64, unique=True)
    password_hash = models.CharField(max_length=255)
    version = models.PositiveIntegerField(default=1)
    failed_logins = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CustomerAuthSession(models.Model):
    """Extra secret AND active GuestSession both required to claim a Tab."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    credential = models.ForeignKey(
        CustomerCredential, on_delete=models.PROTECT, related_name="sessions"
    )
    guest_session = models.ForeignKey(
        GuestSession, on_delete=models.PROTECT, related_name="customer_auth_sessions"
    )
    venue = models.ForeignKey("venue.Venue", on_delete=models.PROTECT)
    credential_version = models.PositiveIntegerField()
    token_digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = (
            models.Index(fields=("guest_session", "revoked_at"),
                         name="guest_customer_session_idx"),
        )
