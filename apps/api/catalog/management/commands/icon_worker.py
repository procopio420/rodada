from time import sleep

from django.core.management.base import BaseCommand

from catalog.services import generate_pending_icons


class Command(BaseCommand):
    help = "Generate persistent canonical-item icons using the configured development provider."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        while True:
            generate_pending_icons()
            if options["once"]:
                return
            sleep(2)
