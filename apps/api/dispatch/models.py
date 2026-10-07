from django.db import models


class DispatchTask(models.Model):
    class Type(models.TextChoices):
        SERVICE_REQUEST = "SERVICE_REQUEST", "Service request"
        DELIVERY = "DELIVERY", "Delivery"
        BILL_REQUEST = "BILL_REQUEST", "Bill request"
        EXCEPTION = "EXCEPTION", "Exception"
    class State(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLAIMED = "CLAIMED", "Claimed"
        DONE = "DONE", "Done"
        CANCELLED = "CANCELLED", "Cancelled"

    venue = models.ForeignKey("pos.Venue", on_delete=models.PROTECT, related_name="dispatch_tasks")
    tab = models.ForeignKey("pos.Tab", null=True, blank=True, on_delete=models.PROTECT, related_name="dispatch_tasks")
    order_item = models.OneToOneField("pos.OrderItem", null=True, blank=True, on_delete=models.PROTECT, related_name="delivery_task")
    service_point = models.ForeignKey("pos.ServicePoint", null=True, blank=True, on_delete=models.SET_NULL, related_name="dispatch_tasks")
    zone = models.ForeignKey("pos.Zone", null=True, blank=True, on_delete=models.SET_NULL, related_name="dispatch_tasks")
    type = models.CharField(max_length=20, choices=Type.choices)
    state = models.CharField(max_length=12, choices=State.choices, default=State.OPEN)
    priority = models.PositiveSmallIntegerField(default=0)
    note = models.TextField(blank=True)
    claimed_by = models.ForeignKey("pos.StaffMember", null=True, blank=True, on_delete=models.SET_NULL, related_name="claimed_tasks")
    created_at = models.DateTimeField(auto_now_add=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    done_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-priority", "created_at", "id"]


class DeliveryRun(models.Model):
    venue = models.ForeignKey("pos.Venue", on_delete=models.PROTECT, related_name="delivery_runs")
    zone = models.ForeignKey("pos.Zone", on_delete=models.PROTECT, related_name="delivery_runs")
    created_by = models.ForeignKey("pos.StaffMember", null=True, on_delete=models.SET_NULL, related_name="created_runs")
    tasks = models.ManyToManyField(DispatchTask, related_name="runs")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)


class DispatchEvent(models.Model):
    venue = models.ForeignKey("pos.Venue", on_delete=models.PROTECT, related_name="dispatch_events")
    task = models.ForeignKey(DispatchTask, on_delete=models.PROTECT, related_name="events")
    kind = models.CharField(max_length=40)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
