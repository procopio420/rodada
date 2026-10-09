from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from unittest import skipUnless

from django.db import close_old_connections, connection, transaction
from django.test import TransactionTestCase

from modules.catalog.models import (
    ModifierGroup,
    ModifierOption,
    Product,
    ProductModifierGroup,
    ProductVariant,
)
from modules.ledger.models import Charge
from modules.ordering.models import OrderItem, Tab
from modules.ordering.services import OrderingServiceError, confirm_order
from modules.venue.models import Venue


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks")
class CustomizationConcurrencyTests(TransactionTestCase):
    def setUp(self):
        venue = Venue.objects.create(name="Concurrent", slug="custom-concurrent")
        self.product = Product.objects.create(
            venue=venue, name="Burger", price_cents=2000, fulfillment_station="KITCHEN"
        )
        self.variant = ProductVariant.objects.create(
            product=self.product, name="Duplo", price_cents=3000
        )
        group = ModifierGroup.objects.create(
            venue=venue, name="Extras", selection_mode="MULTI", max_selections=2
        )
        ProductModifierGroup.objects.create(product=self.product, group=group)
        self.option = ModifierOption.objects.create(
            group=group, name="Bacon", price_delta_cents=500
        )
        self.tab = Tab.objects.create(venue=venue, operating_limit_cents=100000)
        self.line = {
            "product_id": self.product.pk,
            "quantity": 2,
            "variant_id": self.variant.pk,
            "modifier_option_ids": [self.option.pk],
        }

    def confirm(self):
        return confirm_order(
            tab_id=self.tab.pk, source="STAFF", lines=[self.line], idempotency_key="same-intent"
        )

    def test_availability_transaction_commits_before_blocked_confirmation_validates(self):
        locked, release, started = Event(), Event(), Event()

        def availability():
            close_old_connections()
            try:
                with transaction.atomic():
                    Product.objects.select_for_update().get(pk=self.product.pk)
                    ModifierOption.objects.filter(pk=self.option.pk).update(
                        availability="UNAVAILABLE"
                    )
                    locked.set()
                    assert release.wait(10)
            finally:
                close_old_connections()

        def ordering():
            close_old_connections()
            try:
                started.set()
                try:
                    self.confirm()
                except OrderingServiceError as error:
                    return error.code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            change = pool.submit(availability)
            assert locked.wait(10)
            order = pool.submit(ordering)
            assert started.wait(10)
            release.set()
            change.result(10)
            assert order.result(10) == "MODIFIER_UNAVAILABLE"
        assert not OrderItem.objects.exists() and not Charge.objects.exists()

    def test_concurrent_identical_intents_charge_once(self):
        barrier = Barrier(2)

        def ordering(_):
            close_old_connections()
            try:
                barrier.wait(10)
                return self.confirm().pk
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(ordering, range(2)))
        assert ids[0] == ids[1]
        assert Charge.objects.count() == 1 and Charge.objects.get().amount_cents == 7000
