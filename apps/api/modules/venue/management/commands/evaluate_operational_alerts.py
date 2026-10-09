from django.core.management.base import BaseCommand
from modules.venue.models import Venue
from modules.management.alerts import evaluate_alerts


class Command(BaseCommand):
    help = 'Rebuild current canonical operational alert episodes; safe to repeat.'

    def handle(self, *args, **options):
        total = sum(evaluate_alerts(venue).count() for venue in Venue.objects.all())
        self.stdout.write(f'{total} active operational alerts')
