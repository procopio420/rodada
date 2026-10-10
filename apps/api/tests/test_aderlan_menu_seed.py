import io

from django.core.management import call_command
from django.test import TestCase

from modules.catalog.models import FulfillmentStation, Product
from modules.venue.models import Venue


class AderlanMenuSeedTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Bar do Aderlan", slug="bar-do-aderlan")

    def seed(self):
        out = io.StringIO()
        call_command("seed_demo_catalog", stdout=out)
        return out.getvalue()

    def test_aderlan_menu_has_full_photo_transcription_with_pricing_and_station(self):
        self.seed()
        products = Product.objects.filter(venue=self.venue)
        assert products.count() == 143
        assert products.filter(fulfillment_station=FulfillmentStation.BAR).count() == 112
        assert products.filter(fulfillment_station=FulfillmentStation.KITCHEN).count() == 31
        cases = [
            ("Camarão com Catupiry", 2500, FulfillmentStation.KITCHEN),
            ("Arroz Negro com Frutos do Mar", 3500, FulfillmentStation.KITCHEN),
            ("Paleta Suína Defumada - Inteira", 12000, FulfillmentStation.KITCHEN),
            ("Paleta Suína Defumada - Meia", 7000, FulfillmentStation.KITCHEN),
            ("Coxinha de Queijo com Alho", 350, FulfillmentStation.KITCHEN),
            ("Brahma 600ml", 1200, FulfillmentStation.BAR),
            ("Brahma 300ml", 600, FulfillmentStation.BAR),
            ("Whisky Black Label (garrafa)", 30000, FulfillmentStation.BAR),
            ("Pinga com Mel (dose)", 500, FulfillmentStation.BAR),
            ("Pinga com Mel (drink)", 1000, FulfillmentStation.BAR),
            ("Red Bull 355ml", 2500, FulfillmentStation.BAR),
        ]
        for name, cents, station in cases:
            with self.subTest(name=name):
                product = products.get(name=name)
                assert product.price_cents == cents
                assert product.fulfillment_station == station
                assert product.active is True
                assert product.icon.pk == product.pk

    def test_reseed_does_not_overwrite_staff_price_or_duplicate_products(self):
        self.seed()
        product = Product.objects.get(venue=self.venue, name="Brahma 600ml")
        original_id = product.id
        product.price_cents = 1400
        product.save(update_fields=["price_cents"])
        product.availability.state = "UNAVAILABLE"
        product.availability.save(update_fields=["state"])
        self.seed()
        product.refresh_from_db()
        assert Product.objects.filter(venue=self.venue).count() == 143
        assert product.id == original_id
        assert product.price_cents == 1400
        assert product.availability.state == "UNAVAILABLE"

    def test_seed_scoped_to_venue(self):
        other = Venue.objects.create(name="Other", slug="other")
        Product.objects.create(venue=other, name="Brahma 600ml", price_cents=999,
                               fulfillment_station=FulfillmentStation.BAR)
        self.seed()
        assert other.products.count() == 1
        assert other.products.first().price_cents == 999
