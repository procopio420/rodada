# Spec 004 GUEST-006: opt-in credential and independently revocable auth session.
import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("guest_access", "0001_initial"),
        ("house_account", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomerCredential",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("username", models.CharField(max_length=64, unique=True)),
                ("password_hash", models.CharField(max_length=255)),
                ("version", models.PositiveIntegerField(default=1)),
                ("failed_logins", models.PositiveSmallIntegerField(default=0)),
                ("locked_until", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("customer", models.OneToOneField(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="guest_credential", to="house_account.customer",
                )),
            ],
        ),
        migrations.CreateModel(
            name="CustomerAuthSession",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("credential_version", models.PositiveIntegerField()),
                ("token_digest", models.CharField(max_length=64, unique=True)),
                ("expires_at", models.DateTimeField()),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("credential", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="sessions", to="guest_access.customercredential",
                )),
                ("guest_session", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="customer_auth_sessions", to="guest_access.guestsession",
                )),
                ("venue", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to="venue.venue",
                )),
            ],
        ),
        migrations.AddIndex(
            model_name="customerauthsession",
            index=models.Index(fields=("guest_session", "revoked_at"),
                               name="guest_customer_session_idx"),
        ),
    ]
