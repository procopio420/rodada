"""Run periodically against durable pending payments; never creates provider charges."""
from django.core.management.base import BaseCommand
from django.conf import settings
from modules.ledger.models import Payment, PaymentStatus
from modules.payment_provider.registry import provider_for_venue
from modules.payment_provider.services import reconcile_provider_payment


class Command(BaseCommand):
    help = "Reconcile pending integrated payments through authenticated provider lookup"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        pending = Payment.objects.filter(status__in=(
            PaymentStatus.CREATED, PaymentStatus.PENDING, PaymentStatus.PROCESSING,
            PaymentStatus.AUTHORIZED, PaymentStatus.CONFIRMATION_PENDING,
        ), provider__gt="", tab__venue_id__in=getattr(settings, "RODADA_PAYMENT_PROVIDERS", {}).keys())
        ids = list(pending.order_by("received_at").values_list("id", "tab__venue_id")[:options["limit"]])
        resolved = 0
        for payment_id, venue_id in ids:
            payment, _ = reconcile_provider_payment(payment_id=payment_id,
                                                    provider=provider_for_venue(venue_id))
            resolved += payment.status not in (PaymentStatus.CREATED, PaymentStatus.PENDING,
                PaymentStatus.PROCESSING, PaymentStatus.AUTHORIZED, PaymentStatus.CONFIRMATION_PENDING)
        self.stdout.write(f"Checked {len(ids)} payments; resolved {resolved}.")
