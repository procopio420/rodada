"""Delete short-lived UX2 event deduplication receipts, never daily aggregates."""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from modules.venue.models import AttendanceTelemetryReceipt


class Command(BaseCommand):
    help = "Remove anonymous UX2 deduplication IDs older than seven days."

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=7)
        deleted = 0
        while True:
            stale = list(
                AttendanceTelemetryReceipt.objects.filter(received_at__lt=cutoff)
                .order_by("received_at").values_list("pk", flat=True)[:1000]
            )
            if not stale:
                break
            count, _ = AttendanceTelemetryReceipt.objects.filter(pk__in=stale).delete()
            deleted += count
        self.stdout.write(f"Expired UX2 receipt IDs: {deleted}")
