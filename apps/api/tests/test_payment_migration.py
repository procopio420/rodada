from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class PaymentConfirmationTimestampMigrationTests(TransactionTestCase):
    """Exercise an upgrade from the last schema before lifecycle timestamps."""

    migrate_from = [("ledger", "0001_initial"), ("ordering", "0002_order_idempotency"),
                    ("house_account", None)]
    migrate_to = [("ledger", "0004_payment_confirmation_timestamp_invariant")]

    @property
    def executor(self):
        return MigrationExecutor(connection)

    def setUp(self):
        super().setUp()
        self.executor.migrate(self.migrate_from)
        old_apps = self.executor.loader.project_state([node for node in self.migrate_from if node[1] is not None]).apps
        Venue = old_apps.get_model("venue", "Venue")
        StaffMember = old_apps.get_model("access", "StaffMember")
        Tab = old_apps.get_model("ordering", "Tab")
        Payment = old_apps.get_model("ledger", "Payment")
        venue = Venue.objects.create(name="Legacy", slug="legacy-payment-migration")
        staff = StaffMember.objects.create(display_name="Caixa", login_identifier="legacy-caixa")
        tab = Tab.objects.create(venue_id=venue.pk)
        self.payment_id = Payment.objects.create(
            tab_id=tab.pk,
            amount_cents=1250,
            method="CASH",
            idempotency_key="legacy-confirmed-payment",
            received_by_id=staff.pk,
        ).pk

    def test_legacy_confirmed_payment_is_backfilled_from_received_at(self):
        self.executor.migrate(self.migrate_to)
        apps = self.executor.loader.project_state(self.migrate_to).apps
        Payment = apps.get_model("ledger", "Payment")
        payment = Payment.objects.get(pk=self.payment_id)
        self.assertEqual(payment.status, "CONFIRMED")
        self.assertEqual(payment.confirmed_at, payment.received_at)

    def tearDown(self):
        self.executor.migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())
        super().tearDown()
