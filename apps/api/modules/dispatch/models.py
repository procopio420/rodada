import uuid

from django.db import models

from modules.access.models import StaffMember
from modules.hospitality.models import Table, TableOccupancy
from modules.ordering.models import OrderItem
from modules.venue.models import Venue


class DispatchTaskType(models.TextChoices):
    SERVICE_REQUEST = "SERVICE_REQUEST", "Service request"
    DELIVERY = "DELIVERY", "Delivery"
    BILL_REQUEST = "BILL_REQUEST", "Bill request"
    EXCEPTION = "EXCEPTION", "Exception"


class DispatchTaskState(models.TextChoices):
    OPEN = "OPEN", "Open"
    CLAIMED = "CLAIMED", "Claimed"
    DONE = "DONE", "Done"
    CANCELLED = "CANCELLED", "Cancelled"


class DeliveryCompletionSource(models.TextChoices):
    MANUAL = "MANUAL", "Manual"


class DispatchTask(models.Model):
    """Persisted operational work. Delivery work is one task per OrderItem."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="dispatch_tasks")
    task_type = models.CharField(max_length=24, choices=DispatchTaskType.choices)
    state = models.CharField(
        max_length=16,
        choices=DispatchTaskState.choices,
        default=DispatchTaskState.OPEN,
    )
    # A unique relation makes READY event replay and transition retries safe.
    order_item = models.OneToOneField(
        OrderItem,
        on_delete=models.PROTECT,
        related_name="delivery_task",
        null=True,
        blank=True,
    )
    destination_table = models.ForeignKey(
        Table,
        on_delete=models.PROTECT,
        related_name="dispatch_tasks",
        null=True,
        blank=True,
    )
    destination_occupancy = models.ForeignKey(
        TableOccupancy,
        on_delete=models.PROTECT,
        related_name="dispatch_tasks",
        null=True,
        blank=True,
    )
    # This is a snapshot, so releasing/moving a table cannot make a historical
    # delivery task silently point to a different physical destination.
    destination_label = models.CharField(max_length=160, blank=True)
    priority = models.SmallIntegerField(default=0)
    claimed_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="claimed_dispatch_tasks",
        null=True,
        blank=True,
    )
    claimed_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="completed_dispatch_tasks",
        null=True,
        blank=True,
    )
    completion_source = models.CharField(
        max_length=16,
        choices=DeliveryCompletionSource.choices,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-priority", "ready_at", "created_at", "id")
        indexes = [
            models.Index(
                fields=("venue", "task_type", "state", "priority", "ready_at"),
                name="dispatch_queue_idx",
            ),
        ]
