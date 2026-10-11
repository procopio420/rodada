"""Provision the Aderlan venue and the photographed venue menu for local demo.

Existing Products are intentionally not overwritten: reseeding must never reset
an operator-edited price or operational availability on a running demo.
"""
from pathlib import Path
import csv
import re
import tempfile

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from modules.venue.models import Venue
from modules.catalog.models import Product, normalize_product_name


MENU_CSV = Path(__file__).resolve().parents[2] / "data" / "aderlan-menu-2026-10-09.csv"


class Command(BaseCommand):
    help = "Cria o Bar do Aderlan e importa o cardápio fotografado, idempotente e sem apagar alterações."

    def add_arguments(self, parser):
        parser.add_argument("--venue-slug", default="bar-do-aderlan")
        parser.add_argument("--venue-name", default="Bar do Aderlan")

    @transaction.atomic
    def handle(self, *args, **options):
        if not MENU_CSV.is_file():
            raise CommandError(f"CSV do catálogo do Aderlan indisponível: {MENU_CSV}")
        venue, _ = Venue.objects.get_or_create(
            slug=options["venue_slug"],
            defaults={"name": options["venue_name"]},
        )
        # Existing product prices, inactive flags, icons and availability are
        # preserved. The opt-in import command handles reviewed bulk updates.
        with MENU_CSV.open(encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            fields = reader.fieldnames
            rows = list(reader)
        # Explicit compatibility with the photographed seed's old unit spelling.
        # This is not fuzzy matching or automatic merging of arbitrary CSV items.
        for row in rows:
            old_name = re.sub(r"(?<=\d) (ml|L)\b", r"\1", row["name"])
            if old_name == row["name"]:
                continue
            old = Product.objects.filter(venue=venue, normalized_name=normalize_product_name(old_name)).first()
            current = Product.objects.filter(venue=venue, normalized_name=normalize_product_name(row["name"])).first()
            if old and current:
                raise CommandError(f"Duas grafias de {row['name']}; revisar identidades antes de importar.")
            if old:
                row["name"] = old.name
        with tempfile.TemporaryDirectory(prefix="rodada-menu-") as temporary:
            prepared = Path(temporary) / "menu.csv"
            with prepared.open("w", encoding="utf-8", newline="") as target:
                writer = csv.DictWriter(target, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            call_command("import_catalog_csv", "--file", str(prepared),
                         "--venue-slug", venue.slug, "--apply", stdout=self.stdout)
        self.stdout.write(
            self.style.SUCCESS(f"Venue {venue.slug}: cardápio do Aderlan disponível no catálogo demo.")
        )
