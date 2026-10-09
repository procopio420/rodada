from unittest import skipUnless

from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL migration validation")
class SettlementOwnershipMigrationTests(TransactionTestCase):
    def test_existing_settlement_gets_owner_and_database_rejects_duplicate(self):
        executor = MigrationExecutor(connection)
        latest_nodes = executor.loader.graph.leaf_nodes()
        old_nodes = [
            (app, "0008_alter_payment_status" if app == "ledger" else name)
            for app, name in latest_nodes
        ]
        executor.migrate(old_nodes)
        try:
            apps = executor.loader.project_state(old_nodes).apps
            venue = apps.get_model("venue", "Venue").objects.create(
                name="Legacy settlement", slug="legacy-settlement"
            )
            staff = apps.get_model("access", "StaffMember").objects.create(
                display_name="Manager", login_identifier="legacy-settlement"
            )
            tab = apps.get_model("ordering", "Tab").objects.create(venue_id=venue.pk)
            payment = apps.get_model("ledger", "Payment").objects.create(
                tab_id=tab.pk,
                amount_cents=1000,
                method="PIX",
                idempotency_key="legacy",
                received_by_id=staff.pk,
                provider=f"sumup:{venue.pk}:merchant",
                provider_payment_id="checkout-a",
                status="CONFIRMED",
                confirmed_at=timezone.now(),
            )
            apps.get_model("payment_provider", "PaymentAttempt").objects.create(
                payment_id=payment.pk,
                provider=payment.provider,
                idempotency_key="legacy",
                metadata={"transaction_id": "tx-a", "merchant_code": "merchant"},
            )
            target = latest_nodes
            executor = MigrationExecutor(connection)
            executor.migrate(target)
            Payment = executor.loader.project_state(target).apps.get_model("ledger", "Payment")
            migrated = Payment.objects.get(pk=payment.pk)
            self.assertEqual(len(migrated.provider_settlement_key), 64)
            with self.assertRaises(IntegrityError), transaction.atomic():
                Payment.objects.create(
                    tab_id=tab.pk,
                    amount_cents=1000,
                    method="PIX",
                    idempotency_key="second",
                    received_by_id=staff.pk,
                    provider=f"sumup:{venue.pk}:merchant",
                    provider_payment_id="checkout-b",
                    status="CONFIRMED",
                    confirmed_at=timezone.now(),
                    provider_settlement_key=migrated.provider_settlement_key,
                )
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())
