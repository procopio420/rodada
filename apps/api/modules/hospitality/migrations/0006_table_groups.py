# Generated for Spec 004 issue #145 — temporary physical TableGroups.
import uuid

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("hospitality", "0005_tableoccupancy_responsibility_version_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="TableGroup",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("label", models.CharField(blank=True, max_length=80)),
                ("request_key", models.UUIDField()),
                ("fingerprint", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("dissolved_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="created_table_groups", to="access.staffmember",
                )),
                ("dissolved_by", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name="dissolved_table_groups", to="access.staffmember",
                )),
                ("venue", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="table_groups", to="venue.venue",
                )),
            ],
        ),
        migrations.CreateModel(
            name="TableGroupMembership",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("removed_at", models.DateTimeField(blank=True, null=True)),
                ("group", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="memberships", to="hospitality.tablegroup",
                )),
                ("table", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="group_memberships", to="hospitality.table",
                )),
            ],
        ),
        migrations.AddConstraint(
            model_name="tablegroup",
            constraint=models.UniqueConstraint(
                fields=("venue", "created_by", "request_key"),
                name="hospitality_group_request_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="tablegroupmembership",
            constraint=models.UniqueConstraint(
                fields=("group", "table"), name="hospitality_group_member_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="tablegroupmembership",
            constraint=models.UniqueConstraint(
                fields=("table",), condition=Q(removed_at__isnull=True),
                name="hospitality_one_active_table_group",
            ),
        ),
    ]
