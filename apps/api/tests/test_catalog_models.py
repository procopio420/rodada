from django.db import IntegrityError, transaction
from django.test import TestCase

from modules.catalog.models import (
    AvailabilityState,
    FulfillmentStation,
    Product,
)
from modules.catalog.queries import catalog_for_venue
from modules.venue.models import Venue


class CatalogFoundationTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Bar", slug="catalog-bar")
        self.other = Venue.objects.create(name="Outro", slug="catalog-other")

    def product(self, *, venue=None, name="Coca-Cola 350 ml", active=True):
        return Product.objects.create(
            venue=venue or self.venue,
            name=name,
            price_cents=900,
            active=active,
            fulfillment_station=FulfillmentStation.BAR,
        )

    def test_new_product_gets_available_operational_state(self):
        product = self.product()

        product.refresh_from_db()
        assert product.availability.state == AvailabilityState.AVAILABLE
        assert product.active is True

    def test_admin_activation_is_independent_from_operational_availability(self):
        product = self.product(active=False)

        product.availability.state = AvailabilityState.UNAVAILABLE
        product.availability.version += 1
        product.availability.save(update_fields=["state", "version", "changed_at"])

        product.refresh_from_db()
        assert product.active is False
        assert product.availability.state == AvailabilityState.UNAVAILABLE

        product.active = True
        product.save(update_fields=["active", "updated_at"])

        product.refresh_from_db()
        assert product.active is True
        assert product.availability.state == AvailabilityState.UNAVAILABLE

    def test_normalized_name_is_unique_inside_venue(self):
        self.product(name="  Coca-Cola   350 ML ")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.product(name="coca-cola 350 ml")

    def test_same_normalized_name_is_allowed_in_another_venue(self):
        first = self.product(name="Água 500 ml")
        second = self.product(venue=self.other, name=" água   500 ml ")

        assert first.normalized_name == second.normalized_name
        assert first.venue_id != second.venue_id

    def test_shared_catalog_query_is_venue_scoped_and_hides_inactive_by_default(self):
        active = self.product(name="Água", active=True)
        self.product(name="Oculto", active=False)
        self.product(venue=self.other, name="Outro venue", active=True)

        result = list(catalog_for_venue(venue_id=self.venue.id))

        assert [item.id for item in result] == [active.id]
        assert result[0].availability.state == AvailabilityState.AVAILABLE
