import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [("venue", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="StaffMember",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("display_name", models.CharField(max_length=120)),
                ("login_identifier", models.CharField(max_length=120, unique=True)),
                ("pin_hash", models.CharField(blank=True, max_length=255)),
                ("password_hash", models.CharField(blank=True, max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="DeviceRegistration",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("installation_key_hash", models.CharField(max_length=128)),
                ("platform", models.CharField(max_length=32)),
                ("friendly_label", models.CharField(blank=True, max_length=120)),
                ("trust_state", models.CharField(choices=[("UNTRUSTED", "Untrusted"), ("TRUSTED", "Trusted"), ("REVOKED", "Revoked")], default="UNTRUSTED", max_length=16)),
                ("first_seen_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen_at", models.DateTimeField(auto_now=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("revocation_reason", models.CharField(blank=True, max_length=240)),
                ("revoked_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="devices_revoked", to="access.staffmember")),
                ("venue", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="devices", to="venue.venue")),
            ],
        ),
        migrations.CreateModel(
            name="VenueStaffMembership",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("ACTIVE", "Active"), ("SUSPENDED", "Suspended"), ("REVOKED", "Revoked")], default="ACTIVE", max_length=16)),
                ("role", models.CharField(choices=[("STAFF", "Staff"), ("CASHIER", "Cashier"), ("MANAGER", "Manager"), ("OWNER", "Owner")], default="STAFF", max_length=16)),
                ("capability_overrides", models.JSONField(blank=True, default=dict)),
                ("version", models.PositiveIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="memberships_created", to="access.staffmember")),
                ("revoked_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="memberships_revoked", to="access.staffmember")),
                ("staff_member", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="venue_memberships", to="access.staffmember")),
                ("venue", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="staff_memberships", to="venue.venue")),
            ],
        ),
        migrations.CreateModel(
            name="StaffSession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("issued_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("last_seen_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("expires_at", models.DateTimeField()),
                ("recently_reauthenticated_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("revocation_reason", models.CharField(blank=True, max_length=240)),
                ("superseded_at", models.DateTimeField(blank=True, null=True)),
                ("device", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="sessions", to="access.deviceregistration")),
                ("membership", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sessions", to="access.venuestaffmembership")),
                ("staff_member", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sessions", to="access.staffmember")),
                ("venue", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="staff_sessions", to="venue.venue")),
            ],
        ),
        migrations.AddConstraint(
            model_name="deviceregistration",
            constraint=models.UniqueConstraint(fields=("venue", "installation_key_hash"), name="access_unique_venue_device"),
        ),
        migrations.AddIndex(
            model_name="deviceregistration",
            index=models.Index(fields=["venue", "trust_state"], name="access_dev_v_trust_idx"),
        ),
        migrations.AddConstraint(
            model_name="venuestaffmembership",
            constraint=models.UniqueConstraint(fields=("venue", "staff_member"), name="access_unique_venue_staff"),
        ),
        migrations.AddIndex(
            model_name="venuestaffmembership",
            index=models.Index(fields=["venue", "status"], name="access_memb_v_status_idx"),
        ),
        migrations.AddIndex(
            model_name="staffsession",
            index=models.Index(fields=["venue", "staff_member"], name="access_sess_v_staff_idx"),
        ),
        migrations.AddIndex(
            model_name="staffsession",
            index=models.Index(fields=["device", "revoked_at"], name="access_sess_dev_rev_idx"),
        ),
    ]
