"""Official SumUp Checkout/APM and merchant transaction contracts, no POST retries."""

import base64
import json
from decimal import Decimal
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, build_opener

from modules.ledger.models import Payment, PaymentMethod, PaymentStatus

from .adapters import ProviderCapabilities, ProviderResult
from .paytime import NoRedirect


def major(cents):
    if type(cents) is not int or cents < 0:
        raise ValueError("Integer minor units required")
    return Decimal(cents) / Decimal(100)


def minor(amount):
    if isinstance(amount, (float, bool)):
        raise ValueError("Floating point monetary values are not accepted")  # noqa: TRY004
    value = Decimal(str(amount)) * 100
    if not value.is_finite() or value != value.to_integral_value():
        raise ValueError("Invalid provider precision")
    return int(value)


def encode_body(body):
    # Decimal numbers must be JSON numbers, not strings or binary floats.
    if isinstance(body, Decimal):
        return format(body, "f")
    if isinstance(body, dict):
        return "{" + ",".join(json.dumps(k) + ":" + encode_body(v) for k, v in body.items()) + "}"
    if isinstance(body, list):
        return "[" + ",".join(encode_body(v) for v in body) + "]"
    return json.dumps(body)


class SumUpPixProvider:
    capabilities = ProviderCapabilities(pix=True, partial_refund=True)

    def __init__(
        self,
        *,
        venue_id,
        merchant_code,
        access_token,
        payment_type="qr_code_pix",
        expires_seconds=None,
        transport=None,
        simulated=False,
    ):
        if not access_token or not merchant_code or payment_type not in ("pix", "qr_code_pix"):
            raise ValueError("Incomplete SumUp configuration")
        self.venue_id = str(venue_id)
        self.merchant_code = merchant_code
        self.provider_key = f"sumup:{venue_id}:{merchant_code}"
        self.access_token = access_token
        self.payment_type = payment_type
        self.expires_seconds = expires_seconds
        self.transport = transport or self._transport
        self.simulated = simulated

    def _transport(self, method, path, body=None):
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("Invalid SumUp API path")
        request = Request(
            "https://api.sumup.com" + path,
            method=method,
            data=encode_body(body).encode() if body is not None else None,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        with build_opener(NoRedirect()).open(request, timeout=15) as response:
            raw = response.read(1_000_001)
            if not raw:
                return {}
            return json.loads(raw, parse_float=Decimal)

    def _payment(self, payment_id):
        return Payment.objects.get(
            pk=payment_id, tab__venue_id=self.venue_id, provider=self.provider_key
        )

    def _validate_checkout(self, data, payment):
        if (
            data.get("checkout_reference") != str(payment.id)
            or data.get("merchant_code") != self.merchant_code
            or data.get("currency") != payment.currency
            or minor(data.get("amount")) != payment.amount_cents
            or not data.get("id")
            or payment.provider_payment_id not in ("", data["id"])
        ):
            raise ValueError("Checkout does not match merchant payment intent")

    def _result(self, data, payment):
        self._validate_checkout(data, payment)
        status = {
            "PENDING": PaymentStatus.PENDING,
            "FAILED": PaymentStatus.FAILED,
            "EXPIRED": PaymentStatus.EXPIRED,
        }.get(data.get("status"), PaymentStatus.CONFIRMATION_PENDING)
        metadata = {
            "provider_state": data.get("status", "UNKNOWN"),
            "merchant_code": self.merchant_code,
            "simulated": self.simulated,
        }
        if data.get("valid_until"):
            metadata["expires_at"] = data["valid_until"]
        for artefact in data.get(self.payment_type, {}).get("artefacts", []):
            if artefact.get("name") == "code" and isinstance(artefact.get("content"), str):
                metadata["pix_copy_paste"] = artefact["content"]
            if artefact.get("name") == "barcode":
                location = artefact.get("location", "")
                parsed = urlparse(location)
                # Docs contain localhost/sample URLs: never follow those with credentials.
                if (
                    parsed.scheme == "https"
                    and parsed.netloc == "api.sumup.com"
                    and parsed.path.startswith("/v0.1/artefacts/")
                ):
                    metadata["pix_qr_location"] = location
        if data.get("status") == "PAID":
            transactions = data.get("transactions", [])
            ids = {tx.get("id") for tx in transactions if tx.get("id")}
            if len(ids) != 1:
                raise ValueError("Paid checkout requires one authoritative transaction")
            tx = self.transport(
                "GET",
                f"/v2.1/merchants/{quote(self.merchant_code, safe='')}/transactions?"
                + urlencode({"id": ids.pop()}),
            )
            if (
                minor(tx.get("amount")) != payment.amount_cents
                or tx.get("currency") != payment.currency
                or tx.get("merchant_code") != self.merchant_code
                or tx.get("status", tx.get("simple_status")) not in ("SUCCESSFUL", "PAID_OUT")
            ):
                raise ValueError("Unverified transaction settlement")
            status = PaymentStatus.CONFIRMED
            metadata["transaction_id"] = tx["id"]
        return ProviderResult(status=status, provider_payment_id=data["id"], metadata=metadata)

    def start_payment(self, input):
        payment = self._payment(input.payment_id)
        if input.method != PaymentMethod.PIX or input.currency != "BRL":
            raise ValueError("Unsupported SumUp Pix payment")
        body = {
            "checkout_reference": input.payment_id,
            "merchant_code": self.merchant_code,
            "amount": major(input.amount_cents),
            "currency": input.currency,
            "description": "Rodada comanda",
        }
        if self.expires_seconds is not None:
            from datetime import timedelta

            if type(self.expires_seconds) is not int or not 60 <= self.expires_seconds <= 86400:
                raise ValueError("Invalid checkout expiration")
            body["valid_until"] = (
                payment.received_at + timedelta(seconds=self.expires_seconds)
            ).isoformat()
        data = self.transport("POST", "/v0.1/checkouts", body)
        self._validate_checkout(data, payment)
        # Persist identity before APM discovery/process can time out.
        Payment.objects.filter(pk=payment.pk, provider_payment_id="").update(
            provider_payment_id=data["id"]
        )
        payment.provider_payment_id = data["id"]
        methods = self.transport(
            "GET", f"/v0.1/checkouts/{quote(data['id'], safe='')}/payment-methods"
        )
        if self.payment_type not in {item["id"] for item in methods.get("items", [])}:
            return ProviderResult(
                status=PaymentStatus.FAILED,
                provider_payment_id=data["id"],
                error_code="APM_NOT_AVAILABLE",
            )
        return self._result(
            self.transport(
                "PUT",
                f"/v0.1/checkouts/{quote(data['id'], safe='')}",
                {"payment_type": self.payment_type},
            ),
            payment,
        )

    def lookup_payment(self, input):
        payment = self._payment(input.payment_id)
        checkout_id = payment.provider_payment_id
        if not checkout_id:
            matches = self.transport(
                "GET", "/v0.1/checkouts?" + urlencode({"checkout_reference": str(payment.id)})
            )
            matches = [
                data
                for data in matches
                if data.get("checkout_reference") == str(payment.id)
                and data.get("merchant_code") == self.merchant_code
            ]
            if len(matches) != 1:
                return ProviderResult(
                    status=PaymentStatus.CONFIRMATION_PENDING, error_code="CHECKOUT_UNRESOLVED"
                )
            checkout_id = matches[0]["id"]
        return self._result(
            self.transport("GET", f"/v0.1/checkouts/{quote(checkout_id, safe='')}"), payment
        )

    def qr_code(self, provider_payment_id):
        payment = Payment.objects.get(
            provider=self.provider_key, provider_payment_id=provider_payment_id
        )
        attempt = payment.provider_attempts.order_by("started_at").last()
        location = attempt.metadata.get("pix_qr_location", "") if attempt else ""
        parsed = urlparse(location)
        if (
            parsed.scheme != "https"
            or parsed.netloc != "api.sumup.com"
            or not parsed.path.startswith("/v0.1/artefacts/")
        ):
            raise ValueError("QR artifact unavailable")
        req = Request(location, headers={"Authorization": f"Bearer {self.access_token}"})
        with build_opener(NoRedirect()).open(req, timeout=15) as response:
            content_type = response.headers.get_content_type()
            if content_type not in ("image/jpeg", "image/png"):
                raise ValueError("Invalid QR content type")
            return (
                f"data:{content_type};base64," + base64.b64encode(response.read(500_000)).decode()
            )

    def verify_webhook(self, *, payload, signature):
        return False  # No invented signature scheme; polling is authoritative.

    def cancel_payment(self, input):
        payment = self._payment(input.payment_id)
        if not payment.provider_payment_id:
            return ProviderResult(status=PaymentStatus.CONFIRMATION_PENDING)
        data = self.transport(
            "DELETE", f"/v0.1/checkouts/{quote(payment.provider_payment_id, safe='')}"
        )
        # Deactivation isn't assumed to cancel an already processed Pix.
        return self._result(data, payment)

    def request_refund(self, *, transaction_id, amount_cents):
        return self.transport(
            "POST",
            f"/v1.0/merchants/{quote(self.merchant_code, safe='')}/payments/{quote(transaction_id, safe='')}/refunds",
            {"amount": major(amount_cents)},
        )


class SumUpTapToPayProvider(SumUpPixProvider):
    capabilities = ProviderCapabilities(tap_to_pay=True, partial_refund=True)

    def start_payment(self, input):
        self._payment(input.payment_id)
        return ProviderResult(
            status=PaymentStatus.PROCESSING,
            metadata={
                "client_unique_transaction_id": input.payment_id,
                "merchant_code": self.merchant_code,
            },
        )

    def lookup_payment(self, input):
        payment = self._payment(input.payment_id)
        tx = self.transport(
            "GET",
            f"/v2.1/merchants/{quote(self.merchant_code, safe='')}/transactions?"
            + urlencode({"client_transaction_id": str(payment.id)}),
        )
        if (
            tx.get("client_transaction_id") != str(payment.id)
            or tx.get("merchant_code") != self.merchant_code
            or minor(tx.get("amount")) != payment.amount_cents
            or tx.get("currency") != payment.currency
        ):
            raise ValueError("Tap transaction doesn't match intent")
        status = {
            "SUCCESSFUL": PaymentStatus.CONFIRMED,
            "PAID_OUT": PaymentStatus.CONFIRMED,
            "FAILED": PaymentStatus.FAILED,
            "CANCELLED": PaymentStatus.CANCELLED,
        }.get(tx.get("status", tx.get("simple_status")), PaymentStatus.CONFIRMATION_PENDING)
        return ProviderResult(
            status=status,
            provider_payment_id=tx["id"],
            metadata={"transaction_id": tx["id"], "merchant_code": self.merchant_code},
        )
