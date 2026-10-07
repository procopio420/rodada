# The pre-payment-lifecycle schema only supported manual payments.  Those rows
# were therefore received as confirmed money at `received_at`; there is no more
# precise historical confirmation event to recover.
from django.db import migrations, models


CONFIRMED_MONEY_STATUSES = ("CONFIRMED", "PARTIALLY_REFUNDED", "REFUNDED")


def backfill_confirmed_at(apps, schema_editor):
    Payment = apps.get_model("ledger", "Payment")
    Payment.objects.filter(
        status__in=CONFIRMED_MONEY_STATUSES,
        confirmed_at__isnull=True,
    ).update(confirmed_at=models.F("received_at"))


def noop_reverse(apps, schema_editor):
    # `received_at` is the only honest timestamp available for legacy manual
    # payments.  Reversing must not erase migrated historical evidence.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("ledger", "0002_payment_cancelled_at_payment_confirmed_at_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_confirmed_at, noop_reverse),
    ]
