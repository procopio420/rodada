"""Append-only approvals separate from immutable DailyClose observations."""
import uuid
from django.db import migrations, models
from django.db.models import Q
import django.db.models.deletion


def protect_decisions(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("""
            CREATE FUNCTION cash_protect_correction_decisions() RETURNS trigger AS $$
            BEGIN
                IF TG_OP = 'DELETE' THEN
                    RAISE EXCEPTION 'Cash correction requests cannot be deleted';
                END IF;
                IF OLD.status <> 'PENDING' OR NEW.status NOT IN ('APPROVED', 'REJECTED')
                    OR NEW.version <> OLD.version + 1 THEN
                    RAISE EXCEPTION 'Cash correction decisions are immutable';
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER cash_correction_decision_guard
                BEFORE UPDATE OR DELETE ON cash_cashcorrectionrequest
                FOR EACH ROW EXECUTE FUNCTION cash_protect_correction_decisions();
        """)


def unprotect_decisions(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("""
            DROP TRIGGER IF EXISTS cash_correction_decision_guard ON cash_cashcorrectionrequest;
            DROP FUNCTION IF EXISTS cash_protect_correction_decisions();
        """)


class Migration(migrations.Migration):
    dependencies = [("cash", "0003_daily_close")]
    operations = [
        migrations.CreateModel(
            name="CashCorrectionRequest",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("requested_at", models.DateTimeField()),
                ("amount_cents", models.IntegerField()),
                ("reason", models.CharField(max_length=240)),
                ("idempotency_key", models.CharField(max_length=120)),
                ("status", models.CharField(max_length=12, choices=[
                    ("PENDING", "Pending"), ("APPROVED", "Approved"), ("REJECTED", "Rejected")
                ], default="PENDING")),
                ("version", models.PositiveIntegerField(default=1)),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                ("decision_reason", models.CharField(blank=True, max_length=240)),
                ("shift", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="correction_requests", to="cash.cashshift")),
                ("requested_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="cash_corrections_requested", to="access.staffmember")),
                ("decided_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="cash_corrections_decided", to="access.staffmember")),
                ("movement", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="approved_request", to="cash.cashmovement")),
                ("correction_of", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="correction_requests", to="cash.cashmovement")),
            ],
        ),
        migrations.AddConstraint(
            model_name="cashcorrectionrequest",
            constraint=models.UniqueConstraint(fields=("shift", "idempotency_key"), name="cash_correction_request_unique"),
        ),
        migrations.AddConstraint(
            model_name="cashcorrectionrequest",
            constraint=models.CheckConstraint(condition=Q(amount_cents__gt=0) | Q(amount_cents__lt=0), name="cash_correction_request_nonzero"),
        ),
        migrations.AddIndex(
            model_name="cashcorrectionrequest", index=models.Index(fields=("shift", "status"), name="cash_correction_shift_idx"),
        ),
        migrations.RunPython(protect_decisions, unprotect_decisions),
    ]
