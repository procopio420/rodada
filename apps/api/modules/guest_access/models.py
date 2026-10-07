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
