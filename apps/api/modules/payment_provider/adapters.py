"""Provider port and a deterministic test adapter.

This module deliberately has no Paytime SDK/API implementation.  Production
adapters must verify server-side provider responses and webhook signatures
before returning normalized results to the services module.
"""

from dataclasses import dataclass, field
from typing import Protocol

from modules.ledger.models import PaymentStatus


@dataclass(frozen=True)
class ProviderCapabilities:
    tap_to_pay: bool = False
    pix: bool = False
    card_online: bool = False
    partial_refund: bool = False
    tips: bool = False


@dataclass(frozen=True)
class ProviderStartInput:
    payment_id: str
    merchant_reference: str
    amount_cents: int
    currency: str
    method: str
    idempotency_key: str


@dataclass(frozen=True)
class ProviderLookupInput:
    payment_id: str
    merchant_reference: str
    provider_payment_id: str = ""


@dataclass(frozen=True)
class ProviderResult:
    status: str
    provider_payment_id: str = ""
    provider_attempt_id: str = ""
    error_code: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedProviderEvent:
    provider_event_id: str
    event_type: str
    status: str
    merchant_reference: str
    provider_payment_id: str = ""
    provider_attempt_id: str = ""
    metadata: dict = field(default_factory=dict)


class PaymentProvider(Protocol):
    provider_key: str
    capabilities: ProviderCapabilities

    def start_payment(self, input: ProviderStartInput) -> ProviderResult: ...

    def lookup_payment(self, input: ProviderLookupInput) -> ProviderResult: ...

    def verify_webhook(self, *, payload: dict, signature: str) -> bool: ...

    def parse_webhook(self, *, payload: dict) -> NormalizedProviderEvent: ...


class DeterministicPaymentProvider:
    """Deterministic test double, intentionally unavailable as an app provider."""

    provider_key = "test-provider"
    capabilities = ProviderCapabilities(tap_to_pay=True, pix=True, card_online=True)

    def __init__(self, *, start_result: ProviderResult | None = None, lookup_results=None):
        self.start_result = start_result or ProviderResult(status=PaymentStatus.PENDING)
        self.lookup_results = lookup_results or {}
        self.start_calls: list[ProviderStartInput] = []
        self.lookup_calls: list[ProviderLookupInput] = []

    def start_payment(self, input: ProviderStartInput) -> ProviderResult:
        self.start_calls.append(input)
        return self.start_result

    def lookup_payment(self, input: ProviderLookupInput) -> ProviderResult:
        self.lookup_calls.append(input)
        return self.lookup_results.get(input.merchant_reference, self.start_result)

    def verify_webhook(self, *, payload: dict, signature: str) -> bool:
        return signature == "test-valid-signature"

    def parse_webhook(self, *, payload: dict) -> NormalizedProviderEvent:
        return NormalizedProviderEvent(**payload)
