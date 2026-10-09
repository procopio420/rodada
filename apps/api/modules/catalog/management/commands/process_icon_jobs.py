import time
from django.core.management.base import BaseCommand
from modules.catalog.services import run_icon_job


class Command(BaseCommand):
    help = "Process durable Catalog icon jobs outside API requests."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        while True:
            worked = run_icon_job()
            if options["once"]:
                return
            if not worked:
                time.sleep(2)
