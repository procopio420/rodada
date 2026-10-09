from dataclasses import asdict

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.ledger.models import Payment
from modules.ledger.services import totals

from .registry import provider_for_venue
from .services import (
    ProviderServiceError,
    ingest_provider_webhook,
    initiate_provider_payment,
    reconcile_provider_payment,
)


def payment_response(payment, *, replayed=False):
    attempt = payment.provider_attempts.order_by("started_at", "id").last()
    metadata = attempt.metadata if attempt else {}
    return {
        "id": str(payment.id),
        "tab_id": str(payment.tab_id),
        "amount_cents": payment.amount_cents,
        "currency": payment.currency,
        "method": payment.method,
        "status": payment.status,
        "confirmed_at": payment.confirmed_at,
        "simulated": metadata.get("simulated", payment.provider.startswith("simulator:")),
        "replayed": replayed,
        "pix_copy_paste": metadata.get("pix_copy_paste", ""),
        "pix_qr_code": metadata.get("pix_qr_code", ""),
        **totals(payment.tab),
    }


def error_response(error):
    return Response({"code": error.code, "message": error.message}, status=error.status_code)


class PaymentCapabilitiesView(APIView):
    permission_classes = (IsAuthenticated, RequireCapability)
    required_capability = Capability.PAYMENT_COLLECT

    def get(self, request):
        try:
            provider = provider_for_venue(request.actor_context.venue_id)
        except ProviderServiceError:
            return Response(
                {
                    "tap_to_pay": False,
                    "pix": False,
                    "card_online": False,
                    "partial_refund": False,
                    "tips": False,
                }
            )
        capabilities = asdict(provider.capabilities)
        capabilities["simulated"] = getattr(provider, "simulated", False)
        try:
            tap = provider_for_venue(request.actor_context.venue_id, "TAP_TO_PAY")
            assert_tap_authorized(request.actor_context, tap)
            capabilities["tap_to_pay"] = tap.capabilities.tap_to_pay
        except ProviderServiceError:
            capabilities["tap_to_pay"] = False
        return Response(capabilities)


class IntegratedPaymentCreateView(APIView):
    permission_classes = (IsAuthenticated, RequireCapability)
    required_capability = Capability.PAYMENT_COLLECT

    def post(self, request, tab_id):
        try:
            provider = provider_for_venue(
                request.actor_context.venue_id, request.data.get("method", "PIX")
            )
            if request.data.get("method") == "TAP_TO_PAY" and provider.capabilities.tap_to_pay:
                assert_tap_authorized(request.actor_context, provider)
            payment, attempt, replayed = initiate_provider_payment(
                tab_id=tab_id,
                actor=request.actor_context,
                provider=provider,
                amount_cents=request.data.get("amount_cents"),
                method=request.data.get("method", ""),
                idempotency_key=request.data.get("idempotency_key", ""),
            )
        except ProviderServiceError as error:
            return error_response(error)
        if (
            payment.method == "PIX"
            and payment.provider_payment_id
            and not attempt.metadata.get("pix_qr_code")
        ):
            try:
                qr = provider.qr_code(payment.provider_payment_id)
                from django.db import transaction

                with transaction.atomic():
                    locked = type(attempt).objects.select_for_update().get(pk=attempt.pk)
                    locked.metadata = {**locked.metadata, "pix_qr_code": qr}
                    locked.save(update_fields=["metadata"])
            except (OSError, ValueError, KeyError):
                qr = None  # EMV remains usable; QR imagery never determines financial state.
        return Response(
            payment_response(payment, replayed=replayed), status=200 if replayed else 201
        )


class IntegratedPaymentDetailView(APIView):
    permission_classes = (IsAuthenticated, RequireCapability)
    required_capability = Capability.PAYMENT_COLLECT

    def get(self, request, payment_id):
        payment = (
            Payment.objects.select_related("tab")
            .filter(pk=payment_id, tab__venue_id=request.actor_context.venue_id)
            .first()
        )
        if payment is None:
            return Response({"code": "PAYMENT_NOT_FOUND"}, status=404)
        return Response(payment_response(payment))

    def post(self, request, payment_id):
        try:
            existing = Payment.objects.filter(
                pk=payment_id, tab__venue_id=request.actor_context.venue_id
            ).first()
            if existing is None:
                return Response({"code": "PAYMENT_NOT_FOUND"}, status=404)
            payment, _ = reconcile_provider_payment(
                payment_id=payment_id,
                actor=request.actor_context,
                provider=provider_for_venue(
                    request.actor_context.venue_id, existing.method, existing.provider
                ),
            )
        except ProviderServiceError as error:
            return error_response(error)
        return Response(payment_response(payment))


class PaytimeWebhookView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request, venue_id):
        try:
            event, replayed = ingest_provider_webhook(
                provider=provider_for_venue(venue_id, provider_key=f"paytime:{venue_id}"),
                payload=request.data,
                signature=request.headers.get("Authorization", ""),
            )
        except ProviderServiceError as error:
            return error_response(error)
        return Response({"id": str(event.id), "replayed": replayed})


def assert_tap_authorized(actor, provider):
    from modules.access.models import DeviceRegistration

    from .models import DeviceAuthorization

    device = DeviceRegistration.objects.filter(pk=actor.device_id, venue_id=actor.venue_id).first()
    if device is None or device.trust_state != "TRUSTED":
        raise ProviderServiceError(
            "PAYMENT_DEVICE_UNAUTHORIZED", "Autorize este aparelho para cobrança.", 403
        )
    if getattr(provider, "simulated", False):
        return
    if not DeviceAuthorization.objects.filter(
        connection__venue_id=actor.venue_id,
        connection__merchant_code=provider.merchant_code,
        connection__active=True,
        device_id=actor.device_id,
        staff_id=actor.staff_id,
        active=True,
    ).exists():
        raise ProviderServiceError(
            "PAYMENT_DEVICE_UNAUTHORIZED", "Aparelho não autorizado pelo estabelecimento.", 403
        )
    # No token issuance until SumUp approves employee/BYOD delegation.
    raise ProviderServiceError(
        "SUMUP_SDK_ACTIVATION_BLOCKED", "Aproximação aguarda aprovação SumUp.", 409
    )
