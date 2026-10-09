from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class PricingUpgradeTests(TransactionTestCase):
    def test_legacy_adjustments_map_without_rewriting_money(self):
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        old_targets = [(app, name) for app, name in latest if app != "ledger"] + [
            ("ledger", "0008_alter_payment_status")
        ]
        try:
            executor.migrate(old_targets)
            apps = executor.loader.project_state(old_targets).apps
            Venue = apps.get_model("venue", "Venue")
            Staff = apps.get_model("access", "StaffMember")
            Tab = apps.get_model("ordering", "Tab")
            Product = apps.get_model("catalog", "Product")
            Order = apps.get_model("ordering", "Order")
            Item = apps.get_model("ordering", "OrderItem")
            Charge = apps.get_model("ledger", "Charge")
            Adjustment = apps.get_model("ledger", "LedgerAdjustment")
            venue = Venue.objects.create(name="Legacy", slug="legacy-pricing")
            staff = Staff.objects.create(display_name="Legacy", login_identifier="legacy-pricing")
            tab = Tab.objects.create(venue=venue)
            product = Product.objects.create(
                venue=venue, name="Beer", price_cents=1234, fulfillment_station="BAR"
            )
            order = Order.objects.create(tab=tab)
            item = Item.objects.create(
                order=order,
                product=product,
                product_name_snapshot="Beer",
                unit_price_cents=1234,
                quantity=1,
            )
            charge = Charge.objects.create(tab=tab, order_item=item, amount_cents=1234)
            fact = Adjustment.objects.create(
                tab=tab,
                order_item=item,
                kind="ORDER_ITEM_CANCELLATION",
                amount_cents=-1234,
                created_by=staff,
                reason_code="LEGACY",
                idempotency_key="legacy",
            )
            executor = MigrationExecutor(connection)
            executor.migrate(latest)
            apps = executor.loader.project_state(latest).apps
            upgraded = apps.get_model("ledger", "LedgerAdjustment").objects.get(pk=fact.id)
            allocation = apps.get_model("ledger", "AdjustmentAllocation").objects.get(
                adjustment_id=fact.id
            )
            self.assertEqual(
                (upgraded.kind, upgraded.amount_cents, upgraded.reason_code),
                ("ORDER_ITEM_CANCELLATION", -1234, "LEGACY"),
            )
            self.assertEqual(
                (allocation.charge_id, allocation.amount_cents, allocation.basis_cents),
                (charge.id, -1234, 1234),
            )
            self.assertEqual(
                apps.get_model("ledger", "Charge").objects.get(pk=charge.id).amount_cents, 1234
            )
        finally:
            MigrationExecutor(connection).migrate(latest)
