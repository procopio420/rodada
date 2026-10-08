from dataclasses import asdict

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.ledger.models import Payment
from modules.ledger.services import totals
from .registry import provider_for_venue
from .services import (ProviderServiceError, ingest_provider_webhook,
                       initiate_provider_payment, reconcile_provider_payment)


def payment_response(payment, *, replayed=False):
    attempt = payment.provider_attempts.order_by("started_at", "id").last()
    metadata = attempt.metadata if attempt else {}
    return {"id": str(payment.id), "tab_id": str(payment.tab_id),
            "amount_cents": payment.amount_cents, "currency": payment.currency,
            "method": payment.method, "status": payment.status,
            "confirmed_at": payment.confirmed_at, "replayed": replayed,
            "pix_copy_paste": metadata.get("pix_copy_paste", ""),
            "pix_qr_code": metadata.get("pix_qr_code", ""), **totals(payment.tab)}


def error_response(error):
    return Response({"code": error.code, "message": error.message}, status=error.status_code)


class PaymentCapabilitiesView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.PAYMENT_COLLECT

    def get(self, request):
        try:
            provider = provider_for_venue(request.actor_context.venue_id)
        except ProviderServiceError:
            return Response({"tap_to_pay": False, "pix": False, "card_online": False,
                             "partial_refund": False, "tips": False})
        return Response(asdict(provider.capabilities))


class IntegratedPaymentCreateView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.PAYMENT_COLLECT

    def post(self, request, tab_id):
        try:
            provider = provider_for_venue(request.actor_context.venue_id)
            payment, attempt, replayed = initiate_provider_payment(
                tab_id=tab_id, actor=request.actor_context, provider=provider,
                amount_cents=request.data.get("amount_cents"),
                method=request.data.get("method", ""),
                idempotency_key=request.data.get("idempotency_key", ""))
        except ProviderServiceError as error:
            return error_response(error)
        if payment.method == "PIX" and payment.provider_payment_id and not attempt.metadata.get("pix_qr_code"):
            try:
                qr = provider.qr_code(payment.provider_payment_id)
                from django.db import transaction
                with transaction.atomic():
                    locked = type(attempt).objects.select_for_update().get(pk=attempt.pk)
                    locked.metadata = {**locked.metadata, "pix_qr_code": qr}
                    locked.save(update_fields=["metadata"])
            except Exception:
                pass  # EMV remains usable; QR imagery never determines financial state.
        return Response(payment_response(payment, replayed=replayed), status=200 if replayed else 201)


class IntegratedPaymentDetailView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.PAYMENT_COLLECT

    def get(self, request, payment_id):
        payment = Payment.objects.select_related("tab").filter(
            pk=payment_id, tab__venue_id=request.actor_context.venue_id).first()
        if payment is None:
            return Response({"code": "PAYMENT_NOT_FOUND"}, status=404)
        return Response(payment_response(payment))

    def post(self, request, payment_id):
        try:
            payment, _ = reconcile_provider_payment(
                payment_id=payment_id, actor=request.actor_context,
                provider=provider_for_venue(request.actor_context.venue_id))
        except ProviderServiceError as error:
            return error_response(error)
        return Response(payment_response(payment))


class PaytimeWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, venue_id):
        try:
            event, replayed = ingest_provider_webhook(
                provider=provider_for_venue(venue_id), payload=request.data,
                signature=request.headers.get("Authorization", ""))
        except ProviderServiceError as error:
            return error_response(error)
        return Response({"id": str(event.id), "replayed": replayed})
