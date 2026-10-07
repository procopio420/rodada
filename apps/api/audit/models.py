from django.db import models


class AuditEvent(models.Model):
    venue = models.ForeignKey("pos.Venue", on_delete=models.PROTECT, related_name="audit_events")
    actor = models.ForeignKey("pos.StaffMember", null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=80)
    entity_type = models.CharField(max_length=80)
    entity_id = models.PositiveBigIntegerField()
    reason = models.TextField(blank=True)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
