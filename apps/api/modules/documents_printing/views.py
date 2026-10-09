# ruff: noqa: RUF012
# Django/DRF class-level configuration follows the framework contract.
import base64

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability, has_capability
from modules.audit.services import record_audit_event

from .models import PrinterEndpoint, PrintJob, ReceiptDocument, StationPrinterBinding
from .renderers import render_escpos, render_html, render_text
from .services import (
    claim_job,
    create_document,
    finish_attempt,
    operator_action,
    recover_expired,
    request_job,
)


def authorize(request, station=""):
    capability = {"BAR": Capability.PRINT_BAR, "KITCHEN": Capability.PRINT_KITCHEN}.get(
        station, Capability.PRINT_CUSTOMER
    )
    if not has_capability(request.auth.membership, capability):
        raise PermissionDenied("Impressão não autorizada para esta estação/documento.")


def manage(request):
    if not has_capability(request.auth.membership, Capability.PRINT_MANAGE):
        raise PermissionDenied("Gerência de impressão não autorizada.")


def document_payload(document, width=80, reprint=False):
    return {
        "id": str(document.id),
        "source_id": str(document.source_id),
        "template_version": document.template_version,
        "non_fiscal": True,
        "kind": document.kind,
        "source_version": document.source_version,
        "snapshot_hash": document.snapshot_hash,
        "snapshot": document.snapshot,
        "html": render_html(document, width, reprint),
        "text": render_text(document, width, reprint),
    }


def job_payload(job):
    return {
        "id": str(job.id),
        "document_id": str(job.document_id),
        "endpoint_id": str(job.endpoint_id),
        "state": job.state,
        "attempt_count": job.attempt_count,
        "last_error": job.last_error,
        "reprint_of": str(job.reprint_of_id) if job.reprint_of_id else None,
        "reason": job.reason,
        "created_at": job.created_at,
        "available_at": job.available_at,
        "attempts": [
            {
                "number": a.number,
                "outcome": a.outcome,
                "detail": a.detail,
                "started_at": a.started_at,
                "finished_at": a.finished_at,
            }
            for a in job.attempts.order_by("number")
        ],
    }


class DocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        class Input(serializers.Serializer):
            tab_id = serializers.UUIDField()
            kind = serializers.ChoiceField(
                choices=[
                    "CUSTOMER_CHECK",
                    "PAYMENT_RECEIPT",
                    "PARTIAL_PAYMENT_RECEIPT",
                    "CLOSED_TAB_RECEIPT",
                    "PRODUCTION_TICKET",
                ]
            )
            source_id = serializers.UUIDField(required=False)
            station = serializers.ChoiceField(
                choices=["BAR", "KITCHEN"], required=False, default=""
            )
            expected_version = serializers.IntegerField(min_value=1, required=False)

        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        authorize(request, values["station"] if values["kind"] == "PRODUCTION_TICKET" else "")
        from modules.ordering.models import Order, Tab

        tab = get_object_or_404(Tab, id=values["tab_id"], venue=request.auth.venue)
        if values["kind"] == "PRODUCTION_TICKET":
            get_object_or_404(Order, id=values.get("source_id"), tab=tab, status="CONFIRMED")
        else:
            values["station"] = ""
        document = create_document(actor=request.actor_context, **values)
        return Response(document_payload(document), status=201)

    def get(self, request, document_id):
        document = get_object_or_404(ReceiptDocument, pk=document_id, venue=request.auth.venue)
        authorize(request, document.station)
        return Response(document_payload(document))


class EndpointInput(serializers.Serializer):
    id = serializers.UUIDField(required=False)
    label = serializers.CharField(max_length=120)
    adapter = serializers.ChoiceField(choices=PrinterEndpoint.Adapter.values)
    connection_ref = serializers.SlugField(
        max_length=80, required=False, default="", allow_blank=True
    )
    width_mm = serializers.ChoiceField(choices=[58, 80], default=80)
    cut_supported = serializers.BooleanField(default=False)
    enabled = serializers.BooleanField(default=True)
    stations = serializers.ListField(
        child=serializers.ChoiceField(choices=["BAR", "KITCHEN"]), default=[]
    )


class EndpointsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        endpoints = PrinterEndpoint.objects.filter(venue=request.auth.venue).prefetch_related(
            "bindings"
        )
        return Response(
            {
                "results": [
                    {
                        "id": str(e.id),
                        "label": e.label,
                        "adapter": e.adapter,
                        "width_mm": e.width_mm,
                        "enabled": e.enabled,
                        "health": e.health,
                        "health_at": e.health_at,
                        "bridge_status": "LOCAL"
                        if e.adapter == "BROWSER"
                        else "UNKNOWN"
                        if not e.bridge_seen_at
                        else "ONLINE"
                        if (timezone.now() - e.bridge_seen_at).total_seconds() < 30
                        else "OFFLINE",
                        "bridge_seen_at": e.bridge_seen_at,
                        "connection_ref": e.connection_ref,
                        "cut_supported": e.cut_supported,
                        "stations": [b.station for b in e.bindings.all() if b.enabled],
                    }
                    for e in endpoints
                ]
            }
        )

    @transaction.atomic
    def post(self, request):
        manage(request)
        data = EndpointInput(data=request.data)
        data.is_valid(raise_exception=True)
        values = dict(data.validated_data)
        endpoint_id = values.pop("id", None)
        stations = set(values.pop("stations"))
        endpoint = (
            get_object_or_404(
                PrinterEndpoint.objects.select_for_update(),
                pk=endpoint_id,
                venue=request.auth.venue,
            )
            if endpoint_id
            else PrinterEndpoint(venue=request.auth.venue)
        )
        before = {key: getattr(endpoint, key) for key in values} if endpoint_id else None
        if before is not None:
            before["stations"] = list(
                endpoint.bindings.filter(enabled=True).values_list("station", flat=True)
            )
        for key, value in values.items():
            setattr(endpoint, key, value)
        endpoint.health = "UNKNOWN"
        endpoint.health_at = None
        endpoint.save()
        endpoint.bindings.update(enabled=False)
        for station in stations:
            StationPrinterBinding.objects.update_or_create(
                endpoint=endpoint, station=station, defaults={"enabled": True}
            )
        record_audit_event(
            actor=request.actor_context,
            event_type="print.endpoint_configured",
            entity_type="PrinterEndpoint",
            entity_id=str(endpoint.id),
            metadata={"before": before, "after": {**values, "stations": sorted(stations)}},
        )
        return Response({"id": str(endpoint.id)}, status=201)


class JobsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        manage(request)
        recover_expired()

        class Query(serializers.Serializer):
            offset = serializers.IntegerField(min_value=0, default=0)
            failed_only = serializers.BooleanField(default=False)

        query = Query(data=request.query_params)
        query.is_valid(raise_exception=True)
        offset = query.validated_data["offset"]
        jobs = PrintJob.objects.filter(document__venue=request.auth.venue)
        if query.validated_data["failed_only"]:
            jobs = jobs.filter(state__in=["FAILED_RETRYABLE", "FAILED_FINAL", "DELIVERY_UNCERTAIN"])
        rows = list(
            jobs.prefetch_related("attempts").order_by("-created_at", "id")[offset : offset + 101]
        )
        return Response(
            {
                "results": [job_payload(j) for j in rows[:100]],
                "next_offset": offset + 100 if len(rows) > 100 else None,
            }
        )

    def post(self, request):
        class Input(serializers.Serializer):
            document_id = serializers.UUIDField()
            endpoint_id = serializers.UUIDField()
            idempotency_key = serializers.CharField(max_length=120)

        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        document = get_object_or_404(
            ReceiptDocument, pk=values["document_id"], venue=request.auth.venue
        )
        authorize(request, document.station)
        endpoint = get_object_or_404(
            PrinterEndpoint, pk=values["endpoint_id"], venue=request.auth.venue
        )
        job = request_job(
            document=document,
            endpoint=endpoint,
            key=values["idempotency_key"],
            actor=request.actor_context,
        )
        return Response(job_payload(job), status=201)


class JobView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        job = get_object_or_404(
            PrintJob.objects.select_related("document", "endpoint"),
            pk=job_id,
            document__venue=request.auth.venue,
        )
        authorize(request, job.document.station)
        return Response(
            {
                **job_payload(job),
                "output": document_payload(
                    job.document, job.endpoint.width_mm, bool(job.reprint_of_id)
                ),
            }
        )

    def post(self, request, job_id):
        class Input(serializers.Serializer):
            action = serializers.ChoiceField(
                choices=["reprint", "retry", "confirm", "cancel", "browser_open"]
            )
            idempotency_key = serializers.CharField(max_length=120, required=False)
            reason = serializers.CharField(max_length=240, required=False, default="")
            endpoint_id = serializers.UUIDField(required=False)

        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        job = get_object_or_404(
            PrintJob.objects.select_related("document", "endpoint"),
            pk=job_id,
            document__venue=request.auth.venue,
        )
        authorize(request, job.document.station)
        if values["action"] == "reprint":
            endpoint = (
                get_object_or_404(
                    PrinterEndpoint, pk=values["endpoint_id"], venue=request.auth.venue
                )
                if values.get("endpoint_id")
                else job.endpoint
            )
            job = request_job(
                document=job.document,
                endpoint=endpoint,
                key=values.get("idempotency_key", ""),
                actor=request.actor_context,
                reprint_of=job,
                reason=values["reason"],
            )
        else:
            job = operator_action(job.id, values["action"], request.actor_context)
        return Response(job_payload(job))


class BridgeClaimView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        manage(request)

        class Input(serializers.Serializer):
            endpoint_ids = serializers.ListField(
                child=serializers.UUIDField(), allow_empty=False, max_length=20
            )

        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        endpoints = PrinterEndpoint.objects.filter(
            id__in=data.validated_data["endpoint_ids"], venue=request.auth.venue
        ).exclude(adapter="BROWSER")
        endpoints.update(bridge_seen_at=timezone.now())
        recover_expired()
        job = claim_job(list(endpoints.values_list("id", flat=True)))
        if not job:
            return Response(status=204)
        endpoint = job.endpoint
        return Response(
            {
                **job_payload(job),
                "attempt_token": str(job.attempt_token),
                "adapter": endpoint.adapter,
                "connection_ref": endpoint.connection_ref,
                "html": render_html(job.document, endpoint.width_mm, bool(job.reprint_of_id)),
                "escpos": base64.b64encode(
                    render_escpos(
                        job.document,
                        endpoint.width_mm,
                        bool(job.reprint_of_id),
                        endpoint.cut_supported,
                    )
                ).decode(),
            }
        )


class BridgeResultView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        manage(request)

        class Input(serializers.Serializer):
            attempt_token = serializers.UUIDField()
            outcome = serializers.ChoiceField(
                choices=[
                    "OUTPUT_READY",
                    "SPOOL_ACCEPTED",
                    "DELIVERY_UNCERTAIN",
                    "FAILED_RETRYABLE",
                    "FAILED_FINAL",
                ]
            )
            detail = serializers.CharField(max_length=240, default="", allow_blank=True)

        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        get_object_or_404(PrintJob, pk=job_id, document__venue=request.auth.venue)
        accepted = finish_attempt(
            job_id,
            data.validated_data["attempt_token"],
            data.validated_data["outcome"],
            data.validated_data["detail"],
        )
        if accepted:
            job = PrintJob.objects.get(pk=job_id)
            PrinterEndpoint.objects.filter(pk=job.endpoint_id).update(
                health="OFFLINE"
                if data.validated_data["outcome"] == "FAILED_RETRYABLE"
                and job.endpoint.adapter == "NETWORK"
                else "DEGRADED"
                if data.validated_data["outcome"] in ("DELIVERY_UNCERTAIN", "FAILED_FINAL")
                else "UNKNOWN",
                health_at=timezone.now(),
            )
        return Response({"accepted": accepted}, status=200 if accepted else 409)


class ReceiptTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, document_id):
        import hashlib
        import secrets
        from datetime import timedelta

        from .models import ReceiptAccessToken

        document = get_object_or_404(
            ReceiptDocument, pk=document_id, venue=request.auth.venue, station=""
        )
        authorize(request)

        class Input(serializers.Serializer):
            revoke_id = serializers.UUIDField(required=False)

        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        if data.validated_data.get("revoke_id"):
            token = get_object_or_404(
                ReceiptAccessToken, pk=data.validated_data["revoke_id"], document=document
            )
            token.revoked_at = timezone.now()
            token.save(update_fields=["revoked_at"])
            record_audit_event(
                actor=request.actor_context,
                event_type="receipt.share_revoked",
                entity_type="ReceiptAccessToken",
                entity_id=str(token.id),
            )
            return Response({"revoked": True})
        raw = secrets.token_urlsafe(32)
        token = ReceiptAccessToken.objects.create(
            document=document,
            token_hash=hashlib.sha256(raw.encode()).hexdigest(),
            expires_at=timezone.now() + timedelta(hours=24),
            created_by=request.auth.staff_member,
        )
        record_audit_event(
            actor=request.actor_context,
            event_type="receipt.shared",
            entity_type="ReceiptAccessToken",
            entity_id=str(token.id),
        )
        return Response(
            {"id": str(token.id), "token": raw, "expires_at": token.expires_at}, status=201
        )


class SharedReceiptView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, token):
        import hashlib

        from .models import ReceiptAccessToken

        access = get_object_or_404(
            ReceiptAccessToken.objects.select_related("document"),
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at__gt=timezone.now(),
            revoked_at__isnull=True,
            document__station="",
        )
        return Response(
            document_payload(access.document),
            headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"},
        )


class GuestReceiptView(APIView):
    authentication_classes = []
    permission_classes = []

    @transaction.atomic
    def get(self, request):
        from modules.access.context import ActorContext
        from modules.guest_access.services import GuestAccessError, guest_session_context
        from modules.guest_access.views import _error_response

        try:
            session = guest_session_context(
                session_token=request.headers.get("X-Guest-Session", "")
            )
        except GuestAccessError as error:
            return _error_response(error)
        if not session.tab_id:
            return Response(
                {"code": "TAB_REQUIRED", "message": "Abra sua comanda antes de consultar a conta."},
                status=409,
            )
        kind = "CLOSED_TAB_RECEIPT" if session.tab.state == "CLOSED" else "CUSTOMER_CHECK"
        document = create_document(
            tab_id=session.tab_id,
            kind=kind,
            actor=ActorContext(session.table.venue_id, None, None, None),
            guest_session=session,
        )
        return Response(document_payload(document), headers={"Cache-Control": "no-store"})
