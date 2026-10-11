import uuid
from django.db import migrations, models
import django.db.models.deletion


def protect_snapshots(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("""
            CREATE FUNCTION cash_reject_daily_close_mutation() RETURNS trigger AS $$
            BEGIN RAISE EXCEPTION 'DailyClose observations are immutable'; END;
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER cash_daily_close_immutable BEFORE UPDATE OR DELETE ON cash_dailyclose
            FOR EACH ROW EXECUTE FUNCTION cash_reject_daily_close_mutation();
            CREATE TRIGGER cash_daily_close_review_immutable BEFORE UPDATE OR DELETE ON cash_dailyclosereview
            FOR EACH ROW EXECUTE FUNCTION cash_reject_daily_close_mutation();
        """)


def unprotect_snapshots(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute('DROP TRIGGER cash_daily_close_immutable ON cash_dailyclose; DROP TRIGGER cash_daily_close_review_immutable ON cash_dailyclosereview; DROP FUNCTION cash_reject_daily_close_mutation();')


class Migration(migrations.Migration):
    dependencies = [('cash', '0002_movement_kind_direction')]
    operations = [
        migrations.CreateModel(name='DailyClose', fields=[
            ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
            ('business_date', models.DateField()), ('version', models.PositiveIntegerField()),
            ('generated_at', models.DateTimeField()), ('idempotency_key', models.CharField(max_length=120)),
            ('status', models.CharField(max_length=24, choices=[('INCOMPLETE', 'Incomplete'), ('READY_FOR_REVIEW', 'Ready for review')])),
            ('snapshot', models.JSONField()), ('fingerprint', models.CharField(max_length=64)),
            ('venue', models.ForeignKey(to='venue.venue', on_delete=django.db.models.deletion.PROTECT, related_name='daily_closes')),
            ('generated_by', models.ForeignKey(to='access.staffmember', on_delete=django.db.models.deletion.PROTECT)),
        ], options={'constraints':[
            models.UniqueConstraint(fields=('venue', 'business_date', 'version'), name='daily_close_date_version_unique'),
            models.UniqueConstraint(fields=('venue', 'idempotency_key'), name='daily_close_idempotency_unique'),
        ]}),
        migrations.CreateModel(name='DailyCloseReview', fields=[
            ('id', models.BigAutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
            ('reviewed_at', models.DateTimeField()), ('reason', models.CharField(max_length=240)),
            ('fingerprint', models.CharField(max_length=64)),
            ('close', models.OneToOneField(to='cash.dailyclose', on_delete=django.db.models.deletion.PROTECT, related_name='review')),
            ('reviewed_by', models.ForeignKey(to='access.staffmember', on_delete=django.db.models.deletion.PROTECT)),
        ]),
        migrations.RunPython(protect_snapshots, unprotect_snapshots),
    ]
