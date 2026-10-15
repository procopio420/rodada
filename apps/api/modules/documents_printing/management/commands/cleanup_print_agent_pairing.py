"""Bounded cleanup of expired anonymous metadata; never delete approval/audit history."""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from modules.documents_printing.models import PrintAgentThrottle, PrintPairingRequest


class Command(BaseCommand):
    help = "Delete unconsumed pairing requests and throttle windows older than 24h."

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=1)
        requests, _ = PrintPairingRequest.objects.filter(consumed_at__isnull=True, expires_at__lt=cutoff).delete()
        buckets, _ = PrintAgentThrottle.objects.filter(window_started_at__lt=cutoff).delete()
        self.stdout.write(f"Expired anonymous metadata removed: {requests} requests, {buckets} buckets.")
