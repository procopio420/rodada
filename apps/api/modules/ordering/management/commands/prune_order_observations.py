"""Delete expired telemetry only; scheduling is an explicit rollout operation."""
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from modules.ordering.models import OrderClientObservation
from modules.ordering.observations import RETENTION_DAYS


class Command(BaseCommand):
    help = "Prune expired best-effort order observations in bounded batches."

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=1000)
        parser.add_argument("--max-batches", type=int, default=10)

    def handle(self, *args, **options):
        size, batches = options["batch_size"], options["max_batches"]
        if not 1 <= size <= 5000 or not 1 <= batches <= 100:
            raise CommandError("batch-size:1..5000; max-batches:1..100")
        lower = timezone.now() - timedelta(days=RETENTION_DAYS)
        total = 0
        for _ in range(batches):
            with transaction.atomic():
                ids = list(OrderClientObservation.objects.select_for_update(skip_locked=True)
                    .filter(created_at__lt=lower).order_by("id").values_list("id", flat=True)[:size])
                if not ids:
                    break
                count, _ = OrderClientObservation.objects.filter(id__in=ids).delete()
                total += count
        self.stdout.write(f"Deleted {total} expired observation rows; no ordering/ledger facts changed.")
