from django.core.management.base import BaseCommand
from django.utils import timezone

from modules.realtime.models import OutboxEvent
from modules.realtime.services import RETENTION


class Command(BaseCommand):
    help = "Prune only published replay records beyond the 24-hour retention window"

    def handle(self, *args, **options):
        count, _ = OutboxEvent.objects.filter(
            published_at__isnull=False, occurred_at__lt=timezone.now() - RETENTION
        ).delete()
        self.stdout.write(str(count))
