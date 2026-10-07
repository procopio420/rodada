from django.core.management.base import BaseCommand
from django.db import transaction

from modules.catalog.models import FulfillmentStation, Product, normalize_product_name
from modules.venue.models import Venue


DEMO_PRODUCTS = (
    ("Água 500 ml", 500, FulfillmentStation.BAR),
    ("Refrigerante lata", 700, FulfillmentStation.BAR),
    ("Batata frita", 2800, FulfillmentStation.KITCHEN),
)


class Command(BaseCommand):
    help = "Cria um Venue demo e um catálogo mínimo idempotente."

    def add_arguments(self, parser):
        parser.add_argument("--venue-slug", default="bar-do-aderlan")
        parser.add_argument("--venue-name", default="Bar do Aderlan")

    @transaction.atomic
    def handle(self, *args, **options):
        venue, _ = Venue.objects.get_or_create(
            slug=options["venue_slug"],
            defaults={"name": options["venue_name"]},
        )

        created = 0
        for name, price_cents, station in DEMO_PRODUCTS:
            _, was_created = Product.objects.get_or_create(
                venue=venue,
                normalized_name=normalize_product_name(name),
                defaults={
                    "name": name,
                    "price_cents": price_cents,
                    "fulfillment_station": station,
                    "active": True,
                },
            )
            created += int(was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Venue {venue.slug}: {created} produto(s) criado(s), catálogo demo pronto."
            )
        )
