from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class HousePolicyMigrationTests(TransactionTestCase):
    def test_existing_ledger_is_preserved_and_over_limit_tabs_require_action(self):
        executor = MigrationExecutor(connection)
        before = [
            ("house_account", None),
            ("catalog", "0001_initial"),
            ("ordering", "0002_order_idempotency"),
            (
                "ledger",
                "0006_remove_ledgeradjustment_ledger_adjustment_cancellation_negative_and_more",
            ),
        ]
        executor.migrate(before)
        try:
            old = executor.loader.project_state([node for node in before if node[1]]).apps
            venue = old.get_model("venue", "Venue").objects.create(
                name="Legacy house", slug="legacy-house"
            )
            staff = old.get_model("access", "StaffMember").objects.create(
                display_name="Caixa", login_identifier="legacy-house"
            )
            tab = old.get_model("ordering", "Tab").objects.create(venue_id=venue.pk)
            manual = old.get_model("ordering", "Tab").objects.create(
                venue_id=venue.pk, state="REQUIRES_ACTION"
            )
            product = old.get_model("catalog", "Product").objects.create(
                venue_id=venue.pk, name="History", price_cents=5000, fulfillment_station="BAR"
            )
            order = old.get_model("ordering", "Order").objects.create(tab_id=tab.pk, source="STAFF")
            item = old.get_model("ordering", "OrderItem").objects.create(
                order_id=order.pk,
                product_id=product.pk,
                product_name_snapshot="History",
                unit_price_cents=5000,
                quantity=1,
            )
            charge = old.get_model("ledger", "Charge").objects.create(
                tab_id=tab.pk, order_item_id=item.pk, amount_cents=5000
            )
            payment = old.get_model("ledger", "Payment").objects.create(
                tab_id=tab.pk,
                amount_cents=1000,
                method="EXTERNAL_TERMINAL",
                status="CONFIRMED",
                confirmed_at=timezone.now(),
                received_by_id=staff.pk,
                idempotency_key="history",
            )
            after = [("house_account", "0002_seed_policies")]
            MigrationExecutor(connection).migrate(after)
            current = MigrationExecutor(connection).loader.project_state(after).apps
            migrated = current.get_model("ordering", "Tab").objects.get(pk=tab.pk)
            assert migrated.state == "REQUIRES_ACTION"
            assert migrated.action_reasons == ["SPENDING_LIMIT"]
            assert migrated.operating_limit_cents == 3000
            assert migrated.customer_id is None
            assert current.get_model("ordering", "Tab").objects.get(
                pk=manual.pk
            ).action_reasons == ["OTHER_ACTION_REQUIRED"]
            assert (
                current.get_model("house_account", "VenueRelationshipPolicy")
                .objects.filter(venue_id=venue.pk)
                .count()
                == 5
            )
            assert (
                current.get_model("ledger", "Charge").objects.get(pk=charge.pk).amount_cents == 5000
            )
            assert (
                current.get_model("ledger", "Payment").objects.get(pk=payment.pk).amount_cents
                == 1000
            )
            assert (
                current.get_model("ordering", "OrderItem").objects.get(pk=item.pk).unit_price_cents
                == 5000
            )
            assert (
                current.get_model("audit", "AuditEvent")
                .objects.filter(event_type="tab.house_policy_migrated")
                .count()
                == 2
            )
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())
