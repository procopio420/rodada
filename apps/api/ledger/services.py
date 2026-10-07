import os
import secrets

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ledger.models import Payment, PaymentIntent
from pos.services import exposure_cents, record_payment


class PaymentProvider:
    name = "BASE"
    test_mode = False

    def create_intent(self, amount_cents):
        raise NotImplementedError


class TestTapToPayProvider(PaymentProvider):
    name = "TEST"
    test_mode = True

    def create_intent(self, amount_cents):
        return f"test_{secrets.token_urlsafe(18)}"


def provider():
    # Production providers deliberately require a concrete adapter and credential configuration.
    if os.environ.get("PAYMENT_PROVIDER", "TEST") == "TEST":
        return TestTapToPayProvider()
    raise ValidationError("Configured payment provider has no adapter installed.")


@transaction.atomic
def create_intent(tab, amount_cents, method, idempotency_key, initiated_by):
    if amount_cents <= 0 or amount_cents > exposure_cents(tab):
        raise ValidationError("Payment amount must be within the open exposure.")
    existing = PaymentIntent.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        if existing.tab_id != tab.id or existing.amount_cents != amount_cents or existing.method != method:
            raise ValidationError("Idempotency key was already used with different payment details.")
        return existing
    gateway = provider()
    return PaymentIntent.objects.create(tab=tab, amount_cents=amount_cents, method=method, provider=gateway.name,
        provider_reference=gateway.create_intent(amount_cents), idempotency_key=idempotency_key)


@transaction.atomic
def confirm_test_intent(intent, actor):
    if intent.provider != "TEST":
        raise ValidationError("Only the explicit TEST provider can be confirmed from this endpoint.")
    if intent.status == PaymentIntent.Status.SUCCEEDED:
        return intent
    if intent.status != PaymentIntent.Status.PENDING:
        raise ValidationError("Payment intent cannot be confirmed.")
    payment = record_payment(intent.tab_id, actor, amount_cents=intent.amount_cents, method=intent.method,
        idempotency_key=f"provider:{intent.provider_reference}", status=Payment.Status.CONFIRMED)
    intent.status = PaymentIntent.Status.SUCCEEDED
    intent.payment = payment
    intent.completed_at = timezone.now()
    intent.save(update_fields=["status", "payment", "completed_at"])
    return intent
