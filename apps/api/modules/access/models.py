import uuid

from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone

from modules.venue.models import Venue


class StaffMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    display_name = models.CharField(max_length=120)
    login_identifier = models.CharField(max_length=120, unique=True)
    pin_hash = models.CharField(max_length=255, blank=True)
    password_hash = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_pin(self, pin: str) -> None:
        self.pin_hash = make_password(pin, hasher="pbkdf2_sha256")

    def check_pin(self, pin: str) -> bool:
        return bool(self.pin_hash) and check_password(pin, self.pin_hash)

    def __str__(self) -> str:
        return self.display_name


class MembershipStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    SUSPENDED = "SUSPENDED", "Suspended"
    REVOKED = "REVOKED", "Revoked"


class StaffRole(models.TextChoices):
    STAFF = "STAFF", "Staff"
    CASHIER = "CASHIER", "Cashier"
    MANAGER = "MANAGER", "Manager"
    OWNER = "OWNER", "Owner"


class VenueStaffMembership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="staff_memberships")
    staff_member = models.ForeignKey(
        StaffMember, on_delete=models.PROTECT, related_name="venue_memberships"
    )
    status = models.CharField(
        max_length=16, choices=MembershipStatus.choices, default=MembershipStatus.ACTIVE
    )
    role = models.CharField(max_length=16, choices=StaffRole.choices, default=StaffRole.STAFF)
    capability_overrides = models.JSONField(default=dict, blank=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="memberships_created",
        null=True,
        blank=True,
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="memberships_revoked",
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("venue", "staff_member"), name="access_unique_venue_staff"
            )
        ]
        indexes = [
            models.Index(fields=("venue", "status"), name="access_memb_v_status_idx"),
        ]


class DeviceTrustState(models.TextChoices):
    UNTRUSTED = "UNTRUSTED", "Untrusted"
    TRUSTED = "TRUSTED", "Trusted"
    REVOKED = "REVOKED", "Revoked"


class DeviceRegistration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="devices")
    installation_key_hash = models.CharField(max_length=128)
    platform = models.CharField(max_length=32)
    friendly_label = models.CharField(max_length=120, blank=True)
    trust_state = models.CharField(
        max_length=16, choices=DeviceTrustState.choices, default=DeviceTrustState.UNTRUSTED
    )
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        StaffMember,
        on_delete=models.PROTECT,
        related_name="devices_revoked",
        null=True,
        blank=True,
    )
    revocation_reason = models.CharField(max_length=240, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("venue", "installation_key_hash"), name="access_unique_venue_device"
            )
        ]
        indexes = [
            models.Index(fields=("venue", "trust_state"), name="access_dev_v_trust_idx"),
        ]


class StaffSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="staff_sessions")
    staff_member = models.ForeignKey(
        StaffMember, on_delete=models.PROTECT, related_name="sessions"
    )
    membership = models.ForeignKey(
        VenueStaffMembership, on_delete=models.PROTECT, related_name="sessions"
    )
    device = models.ForeignKey(
        DeviceRegistration,
        on_delete=models.PROTECT,
        related_name="sessions",
        null=True,
        blank=True,
    )
    issued_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    recently_reauthenticated_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.CharField(max_length=240, blank=True)
    superseded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=("venue", "staff_member"), name="access_sess_v_staff_idx"),
            models.Index(fields=("device", "revoked_at"), name="access_sess_dev_rev_idx"),
        ]

    @property
    def is_valid(self) -> bool:
        now = timezone.now()
        if self.revoked_at or self.superseded_at or self.expires_at <= now:
            return False
        if not self.staff_member.is_active:
            return False
        if self.membership.status != MembershipStatus.ACTIVE:
            return False
        if self.membership.venue_id != self.venue_id:
            return False
        if self.device_id and self.device.trust_state == DeviceTrustState.REVOKED:
            return False
        return True
