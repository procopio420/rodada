import logging
import time

from django.core.management.base import BaseCommand
from django.db import DatabaseError, close_old_connections

from modules.realtime.services import dispatch_pending

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Publish committed outbox events into the durable SSE replay log"

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        failures = 0
        while True:
            close_old_connections()
            try:
                count = dispatch_pending(1000)
                failures = 0
            except DatabaseError:
                if options["once"]:
                    raise
                failures += 1
                logger.exception("Realtime publication unavailable; durable events will retry")
                time.sleep(min(30, 2 ** min(failures, 5)))
                continue
            if options["once"]:
                self.stdout.write(str(count))
                return
            if not count:
                time.sleep(0.5)
