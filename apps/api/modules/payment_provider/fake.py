"""Explicit development simulator: PostgreSQL state, no network or card data."""

from django.db import transaction

from modules.ledger.models import Payment, PaymentStatus

from .adapters import ProviderCapabilities, ProviderResult
from .models import SimulatedTransaction


class DeterministicFakePaymentProvider:
    capabilities = ProviderCapabilities(tap_to_pay=True, pix=True, partial_refund=True)
    simulated = True

    def __init__(self, *, venue_id, scenario="success"):
        if scenario not in ("success", "failed", "cancelled", "unknown", "expired"):
            raise ValueError("Unknown simulator scenario")
        self.venue_id = str(venue_id)
        self.provider_key = f"simulator:{venue_id}"
        self.scenario = scenario

    def start_payment(self, input):
        payment = Payment.objects.get(
            pk=input.payment_id, tab__venue_id=self.venue_id, provider=self.provider_key
        )
        SimulatedTransaction.objects.get_or_create(
            payment=payment, defaults={"scenario": self.scenario}
        )
        return ProviderResult(
            status=PaymentStatus.PENDING,
            provider_payment_id=f"sim-{payment.pk}",
            metadata={
                "simulated": True,
                "pix_copy_paste": "SIMULATION ONLY - NOT A PIX CODE",
                "client_unique_transaction_id": str(payment.pk),
            },
        )

    @transaction.atomic
    def lookup_payment(self, input):
        remote = SimulatedTransaction.objects.select_for_update().get(
            payment_id=input.payment_id,
            payment__tab__venue_id=self.venue_id,
            payment__provider=self.provider_key,
        )
        remote.lookup_count += 1
        if remote.lookup_count >= 2:
            remote.status = {
                "success": PaymentStatus.CONFIRMED,
                "failed": PaymentStatus.FAILED,
                "cancelled": PaymentStatus.CANCELLED,
                "unknown": PaymentStatus.CONFIRMATION_PENDING,
                "expired": PaymentStatus.EXPIRED,
            }[remote.scenario]
        remote.save(update_fields=["lookup_count", "status"])
        return ProviderResult(
            status=remote.status,
            provider_payment_id=f"sim-{remote.payment_id}",
            metadata={"simulated": True},
        )

    def qr_code(self, provider_payment_id):
        raise ValueError("Simulator never produces a payable Pix QR")

    def verify_webhook(self, *, payload, signature):
        return False
