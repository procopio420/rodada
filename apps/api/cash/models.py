from django.db import models


class CashShift(models.Model):
    venue = models.ForeignKey("pos.Venue", on_delete=models.PROTECT, related_name="cash_shifts")
    opened_by = models.ForeignKey("pos.StaffMember", null=True, on_delete=models.SET_NULL, related_name="opened_shifts")
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_by = models.ForeignKey("pos.StaffMember", null=True, blank=True, on_delete=models.SET_NULL, related_name="closed_shifts")
    closed_at = models.DateTimeField(null=True, blank=True)
    opening_float_cents = models.IntegerField(default=0)
    closing_note = models.TextField(blank=True)
    class Meta: constraints = [models.UniqueConstraint(fields=["venue"], condition=models.Q(closed_at__isnull=True), name="one_open_shift_per_venue")]
