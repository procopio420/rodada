import secrets
import uuid

from django.db import models
from django.db.models import Q

from modules.access.models import StaffMember
from modules.ordering.models import Tab
from modules.venue.models import Venue


def generate_public_token() -> str:
    """A permanent, opaque value suitable for encoding in a physical QR code."""
    return secrets.token_urlsafe(24)


class TableStatus(models.TextChoices):
    AVAILABLE = "AVAILABLE", "Available"
    OCCUPIED = "OCCUPIED", "Occupied"
    DIRTY = "DIRTY", "Dirty"
    CLEANING = "CLEANING", "Cleaning"
    OUT_OF_SERVICE = "OUT_OF_SERVICE", "Out of service"


class GuestOrderingMode(models.TextChoices):
    DISABLED = "DISABLED", "Disabled"
    JOIN_ACTIVE = "JOIN_ACTIVE", "Join active"
    DIRECT = "DIRECT", "Direct"


class Zone(models.Model):
    """A venue-scoped textual operational area, not a financial owner."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="hospitality_zones")
    label = models.CharField(max_length=80)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("label", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("venue", "label"), name="hospitality_zone_venue_label_uniq"
            ),
        ]
        indexes = [
            models.Index(fields=("venue", "is_active"), name="hospitality_zone_active_idx"),
        ]


class Table(models.Model):
    """A physical resource. It deliberately has no financial relationships."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="tables")
    label = models.CharField(max_length=80)
    zone = models.ForeignKey(
        Zone,
        on_delete=models.SET_NULL,
        related_name="tables",
        null=True,
        blank=True,
    )
    public_token = models.CharField(max_length=64, unique=True, default=generate_public_token)
    access_generation = models.PositiveIntegerField(default=1)
    guest_ordering_mode = models.CharField(
        max_length=16,
        choices=GuestOrderingMode.choices,
        default=GuestOrderingMode.DISABLED,
    )
    guest_ordering_blocked = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=TableStatus.choices,
        default=TableStatus.AVAILABLE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("label", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("venue", "label"), name="hospitality_table_venue_label_uniq"
            ),
        ]
        indexes = [
            models.Index(fields=("venue", "status"), name="hospitality_table_status_idx"),
        ]


class TableOccupancy(models.Model):
    """One visit at one table; Tabs are assigned through immutable-ish history."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    table = models.ForeignKey(Table, on_delete=models.PROTECT, related_name="occupancies")
    responsible_staff = models.ForeignKey(
        StaffMember,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="responsible_occupancies",
    )
    responsible_since = models.DateTimeField(null=True, blank=True)
    responsibility_version = models.PositiveIntegerField(default=0)
    generation = models.PositiveIntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
    released_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="table_occupancies_released",
        null=True,
        blank=True,
    )
    cleaning_started_at = models.DateTimeField(null=True, blank=True)
    cleaning_started_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="table_occupancies_cleaning_started",
        null=True,
        blank=True,
    )
    ready_at = models.DateTimeField(null=True, blank=True)
    ready_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="table_occupancies_ready",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-started_at", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("table",),
                condition=Q(released_at__isnull=True),
                name="hospitality_one_active_occupancy",
            ),
        ]
        indexes = [
            models.Index(fields=("table", "started_at"), name="hospitality_occ_table_time_idx"),
        ]


class TabOccupancyAssignment(models.Model):
    """Historical operational placement of a Tab, not a financial transfer."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    occupancy = models.ForeignKey(
        TableOccupancy,
        on_delete=models.PROTECT,
        related_name="tab_assignments",
    )
    tab = models.ForeignKey(Tab, on_delete=models.PROTECT, related_name="occupancy_assignments")
    assigned_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="tab_occupancy_assignments",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("assigned_at", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("occupancy", "tab"),
                condition=Q(released_at__isnull=True),
                name="hospitality_one_tab_per_active_occ",
            ),
            models.UniqueConstraint(
                fields=("tab",),
                condition=Q(released_at__isnull=True),
                name="hospitality_one_active_occ_per_tab",
            ),
        ]
        indexes = [
            models.Index(
                fields=("occupancy", "released_at"), name="hospitality_assignment_occ_idx"
            ),
        ]


class PartySizeObservation(models.Model):
    """Append-only explicit count. No row means UNKNOWN, never one Tab/person."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT)
    occupancy = models.ForeignKey(
        TableOccupancy,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="party_size_observations",
    )
    tab = models.ForeignKey(
        Tab, null=True, blank=True, on_delete=models.PROTECT, related_name="party_size_observations"
    )
    covers_count = models.PositiveIntegerField()
    version = models.PositiveIntegerField()
    source = models.CharField(
        max_length=8, choices=[("STAFF", "Staff"), ("GUEST", "Guest"), ("IMPORTED", "Imported")]
    )
    staff_member = models.ForeignKey(StaffMember, null=True, blank=True, on_delete=models.PROTECT)
    guest_session = models.ForeignKey(
        "guest_access.GuestSession", null=True, blank=True, on_delete=models.PROTECT
    )
    supersedes = models.OneToOneField(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="superseded_by"
    )
    reason = models.CharField(max_length=500, blank=True)
    idempotency_key = models.CharField(max_length=128)
    observed_at = models.DateTimeField()
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-version",)
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(occupancy__isnull=False, tab__isnull=True)
                    | Q(occupancy__isnull=True, tab__isnull=False)
                ),
                name="party_size_one_target",
            ),
            models.CheckConstraint(
                condition=Q(covers_count__gt=0), name="party_size_positive_count"
            ),
            models.UniqueConstraint(fields=("occupancy", "version"), name="party_size_occ_version"),
            models.UniqueConstraint(fields=("tab", "version"), name="party_size_tab_version"),
            models.UniqueConstraint(
                fields=("venue", "idempotency_key"), name="party_size_request_unique"
            ),
        ]


class ServiceCommand(models.Model):
    """Durable staff intent/result. Retained indefinitely; no silent key expiry."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT)
    actor = models.ForeignKey(StaffMember, on_delete=models.PROTECT)
    action = models.CharField(max_length=16)
    key = models.CharField(max_length=128)
    fingerprint = models.CharField(max_length=64)
    result = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("venue", "actor", "action", "key"), name="hospitality_service_intent_unique"
            )
        ]


class TableGroup(models.Model):
    """Temporary physical arrangement; never the owner of a Tab or occupancy."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="table_groups")
    label = models.CharField(max_length=80, blank=True)
    created_by = models.ForeignKey(
        StaffMember, on_delete=models.PROTECT, related_name="created_table_groups"
    )
    request_key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    dissolved_at = models.DateTimeField(null=True, blank=True)
    dissolved_by = models.ForeignKey(
        StaffMember, null=True, blank=True, on_delete=models.PROTECT,
        related_name="dissolved_table_groups",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("venue", "created_by", "request_key"),
                name="hospitality_group_request_unique",
            ),
        ]


class TableGroupMembership(models.Model):
    """An active Table can belong to at most one physical group."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        TableGroup, on_delete=models.PROTECT, related_name="memberships"
    )
    table = models.ForeignKey(
        Table, on_delete=models.PROTECT, related_name="group_memberships"
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    removed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("group", "table"), name="hospitality_group_member_unique"
            ),
            models.UniqueConstraint(
                fields=("table",), condition=Q(removed_at__isnull=True),
                name="hospitality_one_active_table_group",
            ),
        ]
