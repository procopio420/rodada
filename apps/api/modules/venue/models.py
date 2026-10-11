import uuid

from django.db import models


class StationConfiguration(models.Model):
    """Typed routing enablement; existing immutable routing is never rewritten."""

    venue = models.ForeignKey("venue.Venue", on_delete=models.PROTECT)
    station = models.CharField(max_length=16, choices=[("BAR", "Bar"), ("KITCHEN", "Kitchen")])
    enabled = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)
    label = models.CharField(max_length=120, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("venue", "station"), name="venue_station_unique"),
            models.CheckConstraint(condition=models.Q(station__in=("BAR", "KITCHEN")), name="venue_station_valid"),
            models.CheckConstraint(condition=models.Q(version__gte=1), name="venue_station_version_positive"),
        ]


class Venue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=80, unique=True)
    timezone = models.CharField(max_length=64, default="America/Sao_Paulo")
    business_day_cutoff_hour = models.PositiveSmallIntegerField(default=0, db_default=0)
    guest_mutations_blocked = models.BooleanField(default=False)
    guest_policy_version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)
        constraints = [models.CheckConstraint(condition=models.Q(business_day_cutoff_hour__lte=23), name="venue_cutoff_valid_hour")]

    def __str__(self) -> str:
        return self.name


class OperationalAlertPolicy(models.Model):
    venue = models.OneToOneField(Venue, on_delete=models.PROTECT, primary_key=True)
    version = models.PositiveIntegerField(default=1)
    strategic_products = models.ManyToManyField('catalog.Product', blank=True)
    fulfillment_warning_seconds = models.PositiveIntegerField(default=600)
    fulfillment_danger_seconds = models.PositiveIntegerField(default=1200)
    payment_pending_seconds = models.PositiveIntegerField(default=300)
    guest_request_warning_seconds = models.PositiveIntegerField(default=300)
    guest_request_danger_seconds = models.PositiveIntegerField(default=600)

    class Meta:
        constraints = [models.CheckConstraint(
            condition=models.Q(fulfillment_warning_seconds__gt=0) & models.Q(
                fulfillment_danger_seconds__gt=models.F('fulfillment_warning_seconds')),
            name='venue_alert_sla_ordered'), models.CheckConstraint(
            condition=models.Q(guest_request_warning_seconds__gt=0) & models.Q(
                guest_request_danger_seconds__gt=models.F('guest_request_warning_seconds')),
            name='venue_alert_guest_sla_ordered')]


class OperationalAlert(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT)
    rule_key = models.CharField(max_length=40)
    rule_version = models.PositiveIntegerField()
    subject_id = models.UUIDField()
    severity = models.CharField(max_length=8, choices=[('WARNING', 'Warning'), ('DANGER', 'Danger')])
    status = models.CharField(max_length=16, default='ACTIVE', choices=[('ACTIVE', 'Active'), ('ACKNOWLEDGED', 'Acknowledged'), ('RESOLVED', 'Resolved')])
    source = models.JSONField(default=dict)
    first_detected_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    acknowledged_at = models.DateTimeField(null=True)
    acknowledged_by = models.ForeignKey('access.StaffMember', on_delete=models.PROTECT, null=True)
    resolved_at = models.DateTimeField(null=True)
    repeat_of = models.ForeignKey('self', on_delete=models.PROTECT, null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['venue', 'rule_key', 'subject_id'],
            condition=~models.Q(status='RESOLVED'), name='venue_alert_active_unique')]
        indexes = [models.Index(fields=['venue', 'status'], name='venue_alert_status_idx')]


class OperationalAlertEvent(models.Model):
    alert = models.ForeignKey(OperationalAlert, on_delete=models.PROTECT, related_name='history')
    kind = models.CharField(max_length=24)
    occurred_at = models.DateTimeField()
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ['occurred_at', 'id']

