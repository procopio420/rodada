from django.core.management.base import BaseCommand

from modules.documents_printing.services import recover_expired


class Command(BaseCommand):
    help = "Mark expired print sends uncertain, without resubmitting physical output."

    def handle(self, **options):
        recover_expired()
        self.stdout.write("Expired print leases reviewed.")
