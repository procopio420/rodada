"""Additive fleet metadata. Delivery remains owned by PrintJob/PrintAttempt."""

import uuid
from datetime import timedelta
from typing import ClassVar

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class AgentState(models.TextChoices):
    PENDING_PAIRING = "PENDING_PAIRING"
    ONLINE = "ONLINE"
    STALE = "STALE"
    OFFLINE = "OFFLINE"
    REVOKED = "REVOKED"


class PrinterHealth(models.TextChoices):
    UNKNOWN = "UNKNOWN"
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"


class PrinterTransport(models.TextChoices):
    WINDOWS_RAW = "WINDOWS_RAW"
    WINDOWS_DRIVER = "WINDOWS_DRIVER"
    WINDOWS_SHARED = "WINDOWS_SHARED"
    TCP_LAN = "TCP_LAN"


class PrintAgent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    installation_id = models.UUIDField(unique=True)
    installation_proof_hash = models.CharField(max_length=64, blank=True, default="")
    venue = models.ForeignKey("venue.Venue", on_delete=models.PROTECT, null=True)
    device = models.OneToOneField("access.DeviceRegistration", on_delete=models.PROTECT, null=True)
    label = models.CharField(max_length=120)
    platform = models.CharField(max_length=16, default="WINDOWS")
    version = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paired_at = models.DateTimeField(null=True)
    last_seen_at = models.DateTimeField(null=True)
    revoked_at = models.DateTimeField(null=True)

    class Meta:
        constraints: ClassVar = [
            models.CheckConstraint(
                condition=models.Q(platform="WINDOWS"), name="printing_agent_windows"
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(venue__isnull=True, device__isnull=True, paired_at__isnull=True)
                    | models.Q(venue__isnull=False, device__isnull=False, paired_at__isnull=False)
                ),
                name="printing_agent_pairing_consistent",
            ),
        ]

    def clean(self):
        if self.device_id and self.device.venue_id != self.venue_id:
            raise ValidationError("Device and agent must belong to the same Venue.")

    @property
    def state(self) -> str:
        if self.revoked_at or (self.device_id and self.device.trust_state == "REVOKED"):
            return AgentState.REVOKED
        if not self.paired_at:
            return AgentState.PENDING_PAIRING
        if self.last_seen_at is None:
            return AgentState.OFFLINE
        age = timezone.now() - self.last_seen_at
        if age < timedelta(seconds=30):
            return AgentState.ONLINE
        return AgentState.STALE if age < timedelta(seconds=90) else AgentState.OFFLINE

    @property
    def is_authenticated(self) -> bool:
        return True


class PrintPairingRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(PrintAgent, on_delete=models.PROTECT)
    code_hash = models.CharField(max_length=64, unique=True)
    proof_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True)
    approved_by = models.ForeignKey("access.StaffMember", on_delete=models.PROTECT, null=True)
    approved_venue = models.ForeignKey("venue.Venue", on_delete=models.PROTECT, null=True)
    failed_attempts = models.PositiveIntegerField(default=0)
    credential = models.OneToOneField("access.AgentCredential", on_delete=models.PROTECT, null=True)
    activated_at = models.DateTimeField(null=True)

    class Meta:
        constraints: ClassVar = [
            models.CheckConstraint(
                condition=models.Q(expires_at__gt=models.F("created_at")),
                name="printing_pairing_expiry",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        consumed_at__isnull=True,
                        approved_by__isnull=True,
                        approved_venue__isnull=True,
                    )
                    | models.Q(
                        consumed_at__isnull=False,
                        approved_by__isnull=False,
                        approved_venue__isnull=False,
                    )
                ),
                name="printing_pairing_approval_consistent",
            ),
        ]


class DiscoveredPrinter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(PrintAgent, on_delete=models.PROTECT, related_name="printers")
    local_id = models.CharField(max_length=200)
    label = models.CharField(max_length=120)
    queue_name = models.CharField(max_length=240, blank=True)
    transport = models.CharField(max_length=24, choices=PrinterTransport.choices)
    driver_name = models.CharField(max_length=120, blank=True)
    driver_version = models.CharField(max_length=64, blank=True)
    declared_raw_escpos = models.BooleanField(default=False)
    declared_width_mm = models.PositiveSmallIntegerField(null=True)
    health = models.CharField(
        max_length=16, choices=PrinterHealth.choices, default=PrinterHealth.UNKNOWN
    )
    last_seen_at = models.DateTimeField()

    class Meta:
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=("agent", "local_id"), name="printing_discovery_local_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(transport__in=PrinterTransport.values),
                name="printing_discovery_transport",
            ),
            models.CheckConstraint(
                condition=models.Q(health__in=PrinterHealth.values),
                name="printing_discovery_health",
            ),
            models.CheckConstraint(
                condition=models.Q(declared_width_mm__isnull=True)
                | models.Q(declared_width_mm__in=(58, 80)),
                name="printing_discovery_width",
            ),
        ]


class AgentPrinterRoute(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    endpoint = models.ForeignKey("documents_printing.PrinterEndpoint", on_delete=models.PROTECT)
    printer = models.ForeignKey(DiscoveredPrinter, on_delete=models.PROTECT)
    transport = models.CharField(max_length=24, choices=PrinterTransport.choices)
    profile_id = models.SlugField(max_length=80)
    destination = models.CharField(max_length=240)
    port = models.PositiveIntegerField(default=9100)
    priority = models.PositiveIntegerField(default=100)
    enabled = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints: ClassVar = [
            models.UniqueConstraint(fields=("endpoint", "printer"), name="printing_route_unique"),
            models.CheckConstraint(
                condition=models.Q(version__gte=1), name="printing_route_version"
            ),
            models.CheckConstraint(
                condition=models.Q(port__gte=1, port__lte=65535), name="printing_route_port"
            ),
            models.CheckConstraint(
                condition=models.Q(transport__in=PrinterTransport.values),
                name="printing_route_transport",
            ),
        ]

    def clean(self):
        from .agent_contracts import validate_destination

        if self.endpoint.venue_id != self.printer.agent.venue_id:
            raise ValidationError("Route must belong to the agent's Venue.")
        if self.transport != self.printer.transport:
            raise ValidationError("Route transport must match discovered printer.")
        validate_destination(self.transport, self.destination, self.port)


class PrintAgentThrottle(models.Model):
    key_hash = models.CharField(max_length=64, primary_key=True)
    window_started_at = models.DateTimeField()
    count = models.PositiveIntegerField(default=0)
