import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("access", "0001_initial"), ("venue", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="staffsession",
            name="access_token_hash",
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="staffsession",
            name="refresh_token_hash",
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="staffsession",
            name="access_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="PinLoginThrottle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("login_identifier", models.CharField(max_length=120)),
                ("installation_key_hash", models.CharField(blank=True, max_length=64)),
                ("failure_count", models.PositiveIntegerField(default=0)),
                ("blocked_until", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("venue", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pin_login_throttles", to="venue.venue")),
            ],
        ),
        migrations.AddConstraint(
            model_name="pinloginthrottle",
            constraint=models.UniqueConstraint(
                fields=("venue", "login_identifier", "installation_key_hash"),
                name="access_unique_pin_throttle",
            ),
        ),
        migrations.AddIndex(
            model_name="pinloginthrottle",
            index=models.Index(
                fields=["venue", "login_identifier"],
                name="access_pin_v_login_idx",
            ),
        ),
    ]
