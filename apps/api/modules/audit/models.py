import uuid

from django.db import models

from modules.access.models import DeviceRegistration, StaffMember, StaffSession
from modules.venue.models import Venue


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="audit_events")
    event_type = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100, blank=True)
    entity_id = models.CharField(max_length=100, blank=True)
    actor_staff = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    actor_session = models.ForeignKey(
        StaffSession,
        on_delete=models.PROTECT,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    device = models.ForeignKey(
        DeviceRegistration,
        on_delete=models.PROTECT,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    reason = models.CharField(max_length=240, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("occurred_at", "id")
        indexes = [
            models.Index(fields=("venue", "occurred_at"), name="audit_v_occurred_idx"),
            models.Index(fields=("event_type", "occurred_at"), name="audit_type_occ_idx"),
        ]
