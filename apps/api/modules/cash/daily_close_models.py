"""Immutable venue/day observations; review never rewrites financial facts."""
import uuid
from django.db import models


class DailyClose(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey('venue.Venue', on_delete=models.PROTECT, related_name='daily_closes')
    business_date = models.DateField()
    version = models.PositiveIntegerField()
    generated_at = models.DateTimeField()
    generated_by = models.ForeignKey('access.StaffMember', on_delete=models.PROTECT)
    idempotency_key = models.CharField(max_length=120)
    status = models.CharField(max_length=24, choices=[('INCOMPLETE', 'Incomplete'), ('READY_FOR_REVIEW', 'Ready for review')])
    snapshot = models.JSONField()
    fingerprint = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('venue', 'business_date', 'version'), name='daily_close_date_version_unique'),
            models.UniqueConstraint(fields=('venue', 'idempotency_key'), name='daily_close_idempotency_unique'),
        ]


class DailyCloseReview(models.Model):
    close = models.OneToOneField(DailyClose, on_delete=models.PROTECT, related_name='review')
    reviewed_by = models.ForeignKey('access.StaffMember', on_delete=models.PROTECT)
    reviewed_at = models.DateTimeField()
    reason = models.CharField(max_length=240)
    fingerprint = models.CharField(max_length=64)
