import io
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from modules.catalog.models import FulfillmentStation, Product
from modules.venue.models import Venue


class ImportCatalogCsvTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Bar do Aderlan", slug="bar-do-aderlan")
        self.other = Venue.objects.create(name="Outro bar", slug="outro-bar")

    def run_import(self, content, *flags):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "catalog.csv"
            path.write_text(content, encoding="utf-8")
            output = io.StringIO()
            call_command("import_catalog_csv", "--file", str(path), "--venue-slug", self.venue.slug,
                         *flags, stdout=output)
            return output.getvalue()

    def test_dry_run_then_apply_and_repeat_are_idempotent(self):
        csv = (
            "name,category,price_brl,station,description\n"
            "Brahma 600ml,Cervejas,\"R$ 12,50\",BAR,Garrafa 600ml\n"
            "Batata frita,Porções,\"28,00\",COZINHA,Porção\n"
        )
        preview = self.run_import(csv)
        assert "novos=2" in preview
        assert Product.objects.filter(venue=self.venue).count() == 0

        result = self.run_import(csv, "--apply")
        assert "novos=2" in result
        assert Product.objects.filter(venue=self.venue).count() == 2
        beer = Product.objects.get(venue=self.venue, normalized_name="brahma 600ml")
        assert beer.price_cents == 1250
        assert beer.fulfillment_station == FulfillmentStation.BAR
        assert beer.icon.pk == beer.pk
        assert Product.objects.get(name="Batata frita").fulfillment_station == FulfillmentStation.KITCHEN

        again = self.run_import(csv, "--apply")
        assert "iguais=2" in again
        assert Product.objects.filter(venue=self.venue).count() == 2
        assert Product.objects.get(pk=beer.pk).icon.pk == beer.pk

    def test_update_existing_requires_flag_and_preserves_availability(self):
        product = Product.objects.create(
            venue=self.venue, name="Água 500ml", price_cents=500,
            fulfillment_station=FulfillmentStation.BAR, active=False,
        )
        product.availability.state = "UNAVAILABLE"
        product.availability.save(update_fields=["state"])
        csv = "name,category,price_brl,station\nágua  500ML,Bebidas,\"6,50\",BAR\n"
        result = self.run_import(csv, "--apply")
        assert "alterações ignoradas=1" in result
        product.refresh_from_db()
        assert product.price_cents == 500

        result = self.run_import(csv, "--apply", "--update-existing")
        assert "atualizados=1" in result
        product.refresh_from_db()
        assert product.price_cents == 650
        assert product.category == "Bebidas"
        assert product.active is False
        assert product.availability.state == "UNAVAILABLE"
        assert Product.objects.filter(venue=self.venue).count() == 1

    def test_invalid_later_row_rejects_everything(self):
        csv = (
            "name,category,price_brl,station\n"
            "Brahma,Cervejas,\"12,00\",BAR\n"
            "Fritas,Porções,sem-preço,KITCHEN\n"
        )
        with self.assertRaises(CommandError):
            self.run_import(csv, "--apply")
        assert not Product.objects.exists()

    def test_normalized_duplicate_is_rejected(self):
        csv = (
            "name,category,price_brl,station\n"
            "Água,Bebidas,\"5,00\",BAR\n"
            "agua,Bebidas,\"5,00\",BAR\n"
        )
        with self.assertRaisesMessage(CommandError, "duplicado"):
            self.run_import(csv, "--apply")
        assert not Product.objects.exists()

    def test_scoped_to_venue_and_missing_products_are_not_disabled(self):
        other_product = Product.objects.create(
            venue=self.other, name="Água", price_cents=900,
            fulfillment_station=FulfillmentStation.BAR,
        )
        local_product = Product.objects.create(
            venue=self.venue, name="Café", price_cents=400,
            fulfillment_station=FulfillmentStation.BAR,
        )
        csv = "name,category,price_brl,station\nÁgua,Bebidas,\"5,00\",BAR\n"
        self.run_import(csv, "--apply", "--update-existing")
        assert Product.objects.get(pk=other_product.pk).price_cents == 900
        local_product.refresh_from_db()
        assert local_product.active is True
        assert Product.objects.filter(venue=self.venue).count() == 2
