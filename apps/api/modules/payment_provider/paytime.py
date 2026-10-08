"""Paytime REST Pix adapter. No automatic POST retries or raw response logging."""
import base64
import hashlib
import hmac
import json
from urllib.parse import quote, urlparse, urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler

from modules.ledger.models import Payment, PaymentMethod, PaymentStatus
from .adapters import NormalizedProviderEvent, ProviderCapabilities, ProviderResult


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward merchant credentials to a redirect target.


class PaytimePixProvider:
    capabilities = ProviderCapabilities(pix=True)

    def __init__(self, *, venue_id, base_url, integration_key, x_token, bearer_token,
                 establishment_id, webhook_user, webhook_password, transport=None):
        if urlparse(base_url).scheme != "https" or urlparse(base_url).username:
            raise ValueError("Paytime requires an HTTPS API origin")
        if not all((integration_key, x_token, bearer_token, establishment_id,
                    webhook_user, webhook_password)):
            raise ValueError("Incomplete Paytime configuration")
        self.venue_id = str(venue_id)
        self.provider_key = f"paytime:{venue_id}"
        self.base_url = base_url.rstrip("/")
        self.establishment_id = str(establishment_id)
        self.headers = {"integration-key": integration_key, "x-token": x_token,
                        "Authorization": f"Bearer {bearer_token}",
                        "establishment_id": self.establishment_id,
                        "Content-Type": "application/json", "Accept": "application/json"}
        self.webhook_authorization = "Basic " + base64.b64encode(
            f"{webhook_user}:{webhook_password}".encode()).decode()
        self.transport = transport or self._transport

    def _transport(self, method, path, body=None):
        req = Request(self.base_url + path, method=method, headers=self.headers,
                      data=json.dumps(body).encode() if body is not None else None)
        with build_opener(NoRedirect()).open(req, timeout=15) as response:
            return json.loads(response.read(1_000_001))

    def _normalize(self, data, payment):
        if (str(data.get("establishment", {}).get("id")) != self.establishment_id
                or data.get("type") != "PIX"
                or type(data.get("original_amount")) is not int
                or data["original_amount"] != payment.amount_cents
                or not data.get("_id")
                or (payment.provider_payment_id and data["_id"] != payment.provider_payment_id)):
            raise ValueError("Provider transaction does not match persisted intent")
        if data.get("reference_id") not in (None, "", str(payment.id)):
            raise ValueError("Provider merchant reference mismatch")
        # APPROVED is deliberately not sufficient for a Pix receipt.
        status = {"PAID": PaymentStatus.CONFIRMED, "FAILED": PaymentStatus.FAILED,
                  "CANCELED": PaymentStatus.CANCELLED, "PENDING": PaymentStatus.PENDING,
                  "CREATED": PaymentStatus.PENDING}.get(
                      data.get("status"), PaymentStatus.CONFIRMATION_PENDING)
        metadata = {"provider_state": data.get("status", "UNKNOWN")}
        if isinstance(data.get("emv"), str) and data["emv"]:
            metadata["pix_copy_paste"] = data["emv"]
        return ProviderResult(status=status, provider_payment_id=data["_id"], metadata=metadata)

    def start_payment(self, input):
        if input.method != PaymentMethod.PIX or input.currency != "BRL":
            raise ValueError("Unsupported Paytime payment")
        payment = Payment.objects.get(pk=input.payment_id, tab__venue_id=self.venue_id)
        data = self.transport("POST", "/v1/marketplace/transactions", {
            "payment_type": "PIX", "amount": input.amount_cents, "interest": "STORE",
            "reference_id": input.merchant_reference,
        })
        result = self._normalize(data, payment)
        # Save transaction evidence before optional QR I/O can fail.
        return result

    def lookup_payment(self, input):
        payment = Payment.objects.get(pk=input.payment_id, tab__venue_id=self.venue_id)
        provider_id = input.provider_payment_id
        if not provider_id:
            # Query documented filters, then match the exact reference locally. An empty
            # or incomplete search never proves that no charge exists.
            filters = {"type": "PIX", "establishment.id": int(self.establishment_id),
                       "original_amount": payment.amount_cents,
                       "created_at": {"min": payment.received_at.date().isoformat()}}
            matches = []
            for page in range(1, 11):
                listing = self.transport("GET", "/v1/marketplace/transactions?" + urlencode(
                    {"filters": json.dumps(filters), "perPage": 100, "page": page}))
                matches.extend(item for item in listing["data"]
                               if item.get("reference_id") == input.merchant_reference)
                if page >= listing["lastPage"]:
                    break
            else:
                return ProviderResult(status=PaymentStatus.CONFIRMATION_PENDING,
                                      error_code="RECONCILIATION_SEARCH_INCOMPLETE")
            if len(matches) != 1:
                return ProviderResult(status=PaymentStatus.CONFIRMATION_PENDING,
                                      error_code="PROVIDER_REFERENCE_UNRESOLVED")
            provider_id = matches[0]["_id"]
        return self._normalize(self.transport("GET", "/v1/marketplace/transactions/" +
                                             quote(provider_id, safe="")), payment)

    def qr_code(self, provider_payment_id):
        data = self.transport("GET", "/v1/marketplace/transactions/" +
                              quote(provider_payment_id, safe="") + "/qrcode")
        value = data.get("qrcode", "")
        if not isinstance(value, str) or not value.startswith("data:image/"):
            raise ValueError("Invalid provider QR response")
        return value

    def verify_webhook(self, *, payload, signature):
        return hmac.compare_digest(signature.encode(), self.webhook_authorization.encode())

    def parse_webhook(self, *, payload):
        if payload.get("event") not in ("new-sub-transaction", "updated-sub-transaction"):
            raise ValueError("Unsupported Paytime event")
        data = payload["data"]
        # Resolve only an already bound transaction or an explicit merchant reference.
        payment = Payment.objects.filter(provider=self.provider_key,
                                         provider_payment_id=data["_id"]).first()
        if payment is None and data.get("reference_id"):
            payment = Payment.objects.filter(provider=self.provider_key,
                                             pk=data["reference_id"]).first()
        if payment is None:
            raise ValueError("Unknown Paytime transaction; reconciliation required")
        authoritative = self._normalize(self.transport(
            "GET", "/v1/marketplace/transactions/" + quote(data["_id"], safe="")), payment)
        # Paytime supplies no event UUID: stable delivery identity, not card payload hashing.
        event_id = hashlib.sha256(json.dumps(
            [payload["event"], payload.get("event_date"), data["_id"], data.get("status")],
            separators=(",", ":")).encode()).hexdigest()
        return NormalizedProviderEvent(
            provider_event_id=event_id, event_type=payload["event"],
            status=authoritative.status, merchant_reference=str(payment.id),
            provider_payment_id=authoritative.provider_payment_id,
            metadata=authoritative.metadata)
