import hashlib
import uuid
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from modules.audit.services import record_audit_event
from modules.ledger.models import PaymentStatus, Refund, RefundStatus
from modules.ledger.services import totals
from modules.ordering.models import Order, Tab

from .models import PrintAttempt, PrintJob, ReceiptDocument, StationPrinterBinding
from .renderers import canonical_json

KINDS = {
    "CUSTOMER_CHECK",
    "PAYMENT_RECEIPT",
    "PARTIAL_PAYMENT_RECEIPT",
    "CLOSED_TAB_RECEIPT",
    "PRODUCTION_TICKET",
}


def item_data(item):
    return {
        "id": str(item.id),
        "order_id": str(item.order_id),
        "name": item.product_name_snapshot,
        "quantity": item.quantity,
        "unit_price_cents": item.unit_price_cents,
        "total_cents": item.line_total_cents,
        "customization": item.customization_snapshot,
    }


@transaction.atomic
def create_document(
    *, tab_id, kind, actor, source_id=None, station="", expected_version=None, guest_session=None
):
    if kind not in KINDS or (kind == "PRODUCTION_TICKET" and station not in ("BAR", "KITCHEN")):
        raise ValidationError("Tipo de documento/estação inválido.")
    tab = (
        Tab.objects.select_for_update()
        .select_related("venue")
        .get(pk=tab_id, venue_id=actor.venue_id)
    )
    if expected_version is not None and expected_version != tab.version:
        raise ValidationError("Comanda alterada; atualize antes de gerar a conta.")
    if kind == "CLOSED_TAB_RECEIPT" and tab.state != "CLOSED":
        raise ValidationError("Comanda ainda não encerrada.")
    if kind in ("CUSTOMER_CHECK", "CLOSED_TAB_RECEIPT"):
        if source_id is not None and str(source_id) != str(tab.id):
            raise ValidationError("A origem desta conta deve ser a própria comanda.")
        source_id = tab.id
    elif source_id is None:
        raise ValidationError("Referência canônica do pedido/pagamento obrigatória.")
    now = timezone.now()
    local = now.astimezone(ZoneInfo(tab.venue.timezone))
    data = {
        "venue": tab.venue.name,
        "tab_id": str(tab.id),
        "tab_label": tab.display_label or str(tab.id),
        "tab_state": tab.state,
        "tab_version": tab.version,
        "closed_at": tab.closed_at.isoformat() if tab.closed_at else None,
        "business_date": (local - timedelta(hours=tab.venue.business_day_cutoff_hour))
        .date()
        .isoformat(),
        "items": [],
    }
    if kind == "PRODUCTION_TICKET":
        order = Order.objects.filter(pk=source_id, tab=tab, status="CONFIRMED").first()
        if not order:
            raise ValidationError("Pedido canônico confirmado não encontrado.")
        existing = ReceiptDocument.objects.filter(
            venue=tab.venue, kind=kind, source_id=order.id, station=station
        ).first()
        if existing:
            return existing
        items = list(order.items.select_related("product").all())
        # Legacy routing has no immutable station; resolve once, then freeze in document.
        items = [
            i
            for i in items
            if (i.fulfillment_station_snapshot or i.product.fulfillment_station) == station
            and i.state != "CANCELLED"
        ]
        if not items:
            raise ValidationError("Pedido sem itens confirmados nesta estação.")
        data["items"] = [item_data(i) for i in items]
        data["confirmed_at"] = order.confirmed_at.isoformat()
        data.pop("tab_version")
    else:
        # Reuse the canonical responsibility projection, including incoming transferred items.
        from django.db.models import Q

        from modules.ledger.models import Charge
        from modules.tab_operations.models import TabTransferLine
        from modules.tab_operations.services import responsibility

        rows = sorted(responsibility(tab), key=lambda row: row["charge_id"])
        charges = {
            str(c.id): c
            for c in Charge.objects.filter(id__in=[r["charge_id"] for r in rows]).select_related(
                "order_item"
            )
        }
        data["items"] = [
            {
                **item_data(charges[row["charge_id"]].order_item),
                "charge_id": row["charge_id"],
                "original_tab_id": row["original_tab_id"],
                "responsibility_cents": row["available_cents"],
                "allocation_blocker": row["blocker"],
                "allocated": row["original_tab_id"] != str(tab.id)
                or row["available_cents"] != charges[row["charge_id"]].amount_cents,
            }
            for row in rows
        ]
        data["transfers"] = [
            {
                "id": str(line.id),
                "transfer_id": str(line.transfer_id),
                "source_charge_id": str(line.source_charge_id),
                "amount_cents": line.amount_cents,
                "quantity": line.quantity,
                "incoming": line.transfer.destination_tab_id == tab.id,
                "product_name": line.source_charge.order_item.product_name_snapshot,
            }
            for line in TabTransferLine.objects.filter(
                Q(transfer__source_tab=tab) | Q(transfer__destination_tab=tab),
                transfer__status="COMMITTED",
            )
            .select_related("transfer", "source_charge__order_item")
            .order_by("transfer__committed_at", "id")
        ]
        data["totals"] = totals(tab)
        data["adjustments"] = [
            {
                "id": str(a.id),
                "order_item_id": str(a.order_item_id),
                "kind": a.kind,
                "amount_cents": a.amount_cents,
            }
            for a in tab.ledger_adjustments.order_by("created_at", "id")
        ]
        data["payments"] = [
            {
                "id": str(p.id),
                "amount_cents": p.amount_cents,
                "method": p.method,
                "status": p.status,
                "confirmed_at": p.confirmed_at.isoformat(),
                "simulated": p.provider.startswith("simulator:"),
            }
            for p in tab.payments.filter(
                status__in=PaymentStatus.confirmed_money_values()
            ).order_by("confirmed_at", "id")
        ]
        data["refunds"] = [
            {"id": str(r.id), "payment_id": str(r.payment_id), "amount_cents": r.amount_cents}
            for r in Refund.objects.filter(
                payment__tab=tab, status=RefundStatus.CONFIRMED
            ).order_by("confirmed_at", "id")
        ]
        if kind in ("PAYMENT_RECEIPT", "PARTIAL_PAYMENT_RECEIPT"):
            payment = next((p for p in data["payments"] if p["id"] == str(source_id)), None)
            if not payment:
                raise ValidationError("Recibo exige pagamento canônico confirmado.")
            data["payment"] = payment
            if kind == "PARTIAL_PAYMENT_RECEIPT" and data["totals"]["exposure_cents"] <= 0:
                kind = "PAYMENT_RECEIPT"
    # Exclude presentation timestamp/date from source fingerprint: repeated reads reuse a snapshot.
    source_data = {k: v for k, v in data.items() if k != "business_date"}
    version = hashlib.sha256(canonical_json(source_data).encode()).hexdigest()
    existing = ReceiptDocument.objects.filter(
        venue=tab.venue, kind=kind, source_id=source_id, station=station, source_version=version
    ).first()
    if existing:
        return existing
    data["generated_at"] = local.isoformat()
    return ReceiptDocument.objects.create(
        venue=tab.venue,
        tab=tab,
        kind=kind,
        station=station,
        source_id=source_id,
        source_version=version,
        snapshot=data,
        snapshot_hash=hashlib.sha256(canonical_json(data).encode()).hexdigest(),
        created_by_id=actor.staff_id,
        created_guest_session=guest_session,
    )


@transaction.atomic
def request_job(*, document, endpoint, key, actor, reprint_of=None, reason=""):
    # Lock document before endpoint to serialize cross-printer initial production dispatch.
    document = ReceiptDocument.objects.select_for_update().get(pk=document.pk)
    # Serialize endpoint dispatch/idempotency across workers and independent documents.
    endpoint = (
        type(endpoint).objects.select_for_update().get(pk=endpoint.pk, venue_id=actor.venue_id)
    )
    if document.venue_id != actor.venue_id or not endpoint.enabled:
        raise ValidationError("Destino indisponível para este documento.")
    if not key or len(key) > 120:
        raise ValidationError("Chave de idempotência obrigatória (até 120 caracteres).")
    if (
        document.station
        and not StationPrinterBinding.objects.filter(
            endpoint=endpoint, station=document.station, enabled=True
        ).exists()
    ):
        raise ValidationError("Impressora não vinculada à estação.")
    existing = PrintJob.objects.filter(endpoint=endpoint, idempotency_key=key).first()
    if existing:
        if (
            existing.document_id != document.id
            or existing.reprint_of_id != (reprint_of.id if reprint_of else None)
            or existing.reason != reason
        ):
            raise ValidationError("Chave já usada para outra intenção.")
        return existing
    if reprint_of:
        if reprint_of.document_id != document.id or not reason.strip():
            raise ValidationError("Reimpressão exige original e motivo.")
    else:
        initial = PrintJob.objects.filter(document=document, reprint_of__isnull=True)
        if document.kind != "PRODUCTION_TICKET":
            initial = initial.filter(endpoint=endpoint)
        existing = initial.first()
        if existing:
            return existing
    job = PrintJob.objects.create(
        document=document,
        endpoint=endpoint,
        idempotency_key=key,
        requested_by_id=actor.staff_id,
        available_at=timezone.now(),
        reprint_of=reprint_of,
        reason=reason,
        state="OUTPUT_READY" if endpoint.adapter == "BROWSER" else "QUEUED",
        initial_production_key=document.id
        if document.kind == "PRODUCTION_TICKET" and not reprint_of
        else None,
    )
    record_audit_event(
        actor=actor,
        event_type="print.reprinted" if reprint_of else "print.job_queued",
        entity_type="PrintJob",
        entity_id=str(job.id),
        reason=reason,
        metadata={
            "document_id": str(document.id),
            "endpoint_id": str(endpoint.id),
            "reprint_of": str(reprint_of.id) if reprint_of else None,
        },
    )
    return job


@transaction.atomic
def recover_expired():
    now = timezone.now()
    jobs = PrintJob.objects.select_for_update(skip_locked=True).filter(
        state="SENDING", lease_until__lte=now
    )
    for job in jobs:
        PrintAttempt.objects.filter(
            job=job, token=job.attempt_token, finished_at__isnull=True
        ).update(finished_at=now, outcome="DELIVERY_UNCERTAIN", detail="Worker lease expired")
        job.state = "DELIVERY_UNCERTAIN"
        job.last_error = (
            "Entrega interrompida; pode ter impresso. Confira o papel antes de reimprimir."
        )
        job.lease_until = None
        job.save()


@transaction.atomic
def claim_job(endpoint_ids=None):
    query = PrintJob.objects.select_for_update(skip_locked=True).filter(
        state__in=["QUEUED", "FAILED_RETRYABLE"],
        available_at__lte=timezone.now(),
        endpoint__enabled=True,
    )
    if endpoint_ids is not None:
        query = query.filter(endpoint_id__in=endpoint_ids)
    job = query.order_by("available_at", "id").first()
    if not job:
        return None
    job.state = "SENDING"
    job.attempt_count += 1
    job.attempt_token = uuid.uuid4()
    job.lease_until = timezone.now() + timedelta(seconds=60)
    job.save()
    PrintAttempt.objects.create(job=job, number=job.attempt_count, token=job.attempt_token)
    return job


@transaction.atomic
def finish_attempt(job_id, token, outcome, detail=""):
    if outcome not in (
        "OUTPUT_READY",
        "SPOOL_ACCEPTED",
        "DELIVERY_UNCERTAIN",
        "FAILED_RETRYABLE",
        "FAILED_FINAL",
    ):
        raise ValueError("Adapter cannot confirm physical output")
    job = PrintJob.objects.select_for_update().get(pk=job_id)
    if job.state != "SENDING" or job.attempt_token != token:
        return False
    now = timezone.now()
    if job.lease_until is None or job.lease_until <= now:
        job.state = "DELIVERY_UNCERTAIN"
        job.lease_until = None
        job.last_error = "Resultado recebido após o prazo; confira o papel antes de reimprimir."
        job.save()
        PrintAttempt.objects.filter(job=job, token=token).update(
            finished_at=now, outcome="DELIVERY_UNCERTAIN", detail="Late result after lease expiry"
        )
        return False
    PrintAttempt.objects.filter(job=job, token=token).update(
        finished_at=now, outcome=outcome, detail=detail[:240]
    )
    if outcome == "FAILED_RETRYABLE" and job.attempt_count >= 5:
        outcome = "FAILED_FINAL"
    job.state = outcome
    job.last_error = detail[:240]
    job.lease_until = None
    job.available_at = now + timedelta(seconds=min(300, 5 * 2**job.attempt_count))
    job.save()
    return True


@transaction.atomic
def operator_action(job_id, action, actor):
    job = PrintJob.objects.select_for_update().get(pk=job_id, document__venue_id=actor.venue_id)
    if (
        action == "browser_open"
        and job.state == "OUTPUT_READY"
        and job.endpoint.adapter == "BROWSER"
    ):
        job.state = "DELIVERY_UNCERTAIN"
        job.last_error = "Diálogo solicitado; impressão ou cancelamento não confirmados."
    elif action == "retry" and job.state == "FAILED_RETRYABLE":
        job.available_at = timezone.now()
    elif action == "confirm" and job.state in (
        "OUTPUT_READY",
        "SPOOL_ACCEPTED",
        "DELIVERY_UNCERTAIN",
    ):
        job.state = "PRINTED"
    elif action == "cancel" and job.state in (
        "QUEUED",
        "FAILED_RETRYABLE",
        "FAILED_FINAL",
        "DELIVERY_UNCERTAIN",
        "OUTPUT_READY",
        "SPOOL_ACCEPTED",
    ):
        job.state = "CANCELLED"
    else:
        raise ValidationError("Ação incompatível com o estado de entrega.")
    job.save()
    record_audit_event(
        actor=actor, event_type="print." + action, entity_type="PrintJob", entity_id=str(job.id)
    )
    return job
