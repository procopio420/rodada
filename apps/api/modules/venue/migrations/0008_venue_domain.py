from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("venue", "0007_venue_guest_policy")]

    operations = [
        migrations.CreateModel(
            name="VenueDomain",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ("hostname", models.CharField(max_length=253, unique=True)),
                ("is_active", models.BooleanField(default=False)),
                ("is_verified", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("venue", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="domains", to="venue.venue")),
            ],
        ),
    ]
