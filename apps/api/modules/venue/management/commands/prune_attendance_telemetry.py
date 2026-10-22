"""Delete short-lived UX2 event deduplication receipts, never daily aggregates."""
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from modules.venue.models import AttendanceTelemetryReceipt


class Command(BaseCommand):
    help = "Remove anonymous UX2 deduplication IDs older than seven days."

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=1000)
        parser.add_argument("--max-batches", type=int, default=10)

    def handle(self, *args, **options):
        size, batches = options["batch_size"], options["max_batches"]
        if not 1 <= size <= 5000 or not 1 <= batches <= 100:
            raise CommandError("batch-size must be 1..5000; max-batches must be 1..100")
        cutoff = timezone.now() - timedelta(days=7)
        deleted = 0
        for _ in range(batches):
            stale = list(
                AttendanceTelemetryReceipt.objects.filter(received_at__lt=cutoff)
                .order_by("received_at").values_list("pk", flat=True)[:size]
            )
            if not stale:
                break
            count, _ = AttendanceTelemetryReceipt.objects.filter(pk__in=stale).delete()
            deleted += count
        self.stdout.write(f"Expired UX2 receipt IDs: {deleted}")
