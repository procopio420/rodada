from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from modules.ledger.models import Charge, Payment
from modules.ordering.models import Tab
from modules.venue.models import Venue


class SpendingPolicyMigrationTests(TransactionTestCase):
    def test_backfill_and_schema_rollback_preserve_legacy_tabs_and_ledger(self):
        from modules.catalog.models import Product
        from modules.house_account.models import VenueSpendingLimitPolicy
        from modules.ordering.services import confirm_order

        venue = Venue.objects.create(name="Legacy policy", slug="legacy-spending-policy")
        product = Product.objects.create(
            venue=venue, name="Legacy item", price_cents=1000, fulfillment_station="BAR"
        )
        tab = Tab.objects.create(venue=venue)
        confirm_order(
            tab_id=tab.pk, source="STAFF", lines=[{"product_id": product.id, "quantity": 1}]
        )
        Tab.objects.filter(pk=tab.pk).update(
            operating_limit_cents=0, state="REQUIRES_ACTION", action_reasons=["SPENDING_LIMIT"]
        )
        before = list(Tab.objects.filter(venue=venue).values())
        charges = list(Charge.objects.filter(tab=tab).values())
        VenueSpendingLimitPolicy.objects.filter(venue=venue).update(mode="WARN_ONLY", version=3)
        executor = MigrationExecutor(connection)
        leaves = executor.loader.graph.leaf_nodes()
        try:
            executor.migrate([("house_account", "0002_seed_policies")])
            assert (
                "house_account_venuespendinglimitpolicy"
                not in connection.introspection.table_names()
            )
            MigrationExecutor(connection).migrate(
                [("house_account", "0004_backfill_spending_enforce")]
            )
            policy = VenueSpendingLimitPolicy.objects.get(venue=venue)
            assert policy.mode == "ENFORCE" and policy.version == 1
            assert list(Tab.objects.filter(venue=venue).values()) == before
            assert list(Charge.objects.filter(tab=tab).values()) == charges
            assert not Payment.objects.filter(tab=tab).exists()
        finally:
            MigrationExecutor(connection).migrate(leaves)
