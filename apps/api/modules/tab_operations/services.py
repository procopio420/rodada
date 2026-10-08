"""Structural commands serialize on Tab, the existing financial aggregate lock."""
import hashlib
import json
from dataclasses import dataclass

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from modules.access.capabilities import Capability
from modules.audit.services import record_audit_event
from modules.house_account.services import authorize, financial_position, sync_attention
from modules.ledger.models import Charge, PaymentStatus, Refund, RefundStatus
from modules.ledger.services import totals
from modules.ordering.models import Tab, TabState
from .models import ServicePoint, TabOperation, TabTransfer, TabTransferLine


@dataclass(frozen=True)
class OperationError(Exception):
    code: str
    message: str
    status_code: int = 409
    details: dict | None = None


OPEN = (TabState.OPEN, TabState.REQUIRES_ACTION)
FINANCIAL = ("SPLIT", "MOVE_ITEMS", "MERGE")


def transfer_effect(tab):
    lines = TabTransferLine.objects.filter(transfer__status="COMMITTED")
    incoming = lines.filter(transfer__destination_tab=tab).aggregate(v=Sum("amount_cents"))["v"] or 0
    outgoing = lines.filter(transfer__source_tab=tab).aggregate(v=Sum("amount_cents"))["v"] or 0
    return incoming - outgoing


def payment_blocker(tab, *, confirmed=True):
    if confirmed and (tab.payments.filter(status__in=PaymentStatus.confirmed_money_values()).exists()
                      or Refund.objects.filter(payment__tab=tab, status=RefundStatus.CONFIRMED).exists()):
        return "CONFIRMED_PAYMENT", "Esta comanda já tem pagamento confirmado. Use o fluxo de correção/estorno."
    if tab.payments.exclude(status__in=(*PaymentStatus.confirmed_money_values(), PaymentStatus.FAILED, PaymentStatus.CANCELLED)).exists() or Refund.objects.filter(payment__tab=tab, status=RefundStatus.PENDING).exists():
        return "PAYMENT_IN_FLIGHT", "Pagamento/estorno em andamento. Aguarde a reconciliação."
    return None


def responsibility(tab):
    charges = Charge.objects.filter(Q(tab=tab) | Q(transfer_lines__transfer__destination_tab=tab)).distinct().select_related("order_item", "tab")
    rows = []
    for charge in charges:
        incoming = charge.transfer_lines.filter(transfer__destination_tab=tab).aggregate(v=Sum("amount_cents"))["v"] or 0
        outgoing = charge.transfer_lines.filter(transfer__source_tab=tab).aggregate(v=Sum("amount_cents"))["v"] or 0
        adjustment = charge.order_item.ledger_adjustments.aggregate(v=Sum("amount_cents"))["v"] or 0
        amount = (charge.amount_cents + adjustment if charge.tab_id == tab.id else 0) + incoming - outgoing
        # Allocation-aware pricing is not yet available. Never guess on adjusted lines.
        blocker = "ADJUSTED_LINE" if adjustment and charge.transfer_lines.exists() else None
        rows.append({"charge_id": str(charge.id), "order_item_id": str(charge.order_item_id),
                     "original_tab_id": str(charge.tab_id), "product_name": charge.order_item.product_name_snapshot,
                     "unit_price_cents": charge.order_item.unit_price_cents, "original_quantity": charge.order_item.quantity,
                     "available_cents": max(0, amount), "blocker": blocker})
    return rows


def tab_payload(tab):
    from modules.hospitality.models import TabOccupancyAssignment
    assignment = TabOccupancyAssignment.objects.filter(tab=tab, released_at__isnull=True).first()
    return {"id": str(tab.id), "version": tab.version, "state": tab.state,
            "occupancy_id": str(assignment.occupancy_id) if assignment else None,
            "service_point_id": str(tab.service_point_id) if tab.service_point_id else None,
            "merged_into_id": str(tab.merged_into_id) if tab.merged_into_id else None,
            **financial_position(tab)}


def transferability(tab):
    blocker = payment_blocker(tab)
    return {"tab": tab_payload(tab), "lines": responsibility(tab),
            "blocker": {"code": blocker[0], "message": blocker[1]} if blocker else None}


def check_version(tab, expected):
    if tab.version != expected:
        raise OperationError("VERSION_CONFLICT", "A comanda mudou. Atualize e confira a seleção.", details={"current": transferability(tab)})


def check_open(tab):
    if tab.state not in OPEN:
        raise OperationError("TAB_NOT_OPEN", "Comanda não está aberta.")


def check_payment(tab):
    blocker = payment_blocker(tab)
    if blocker:
        raise OperationError(*blocker)


def selected_lines(source, destination, data):
    check_open(source)
    check_payment(source)
    if destination:
        check_open(destination)
        check_payment(destination)
    rows = {row["charge_id"]: row for row in responsibility(source)}
    selection = data.get("lines", [])
    if data["kind"] == "MERGE":
        selection = [{"charge_id": key, "amount_cents": row["available_cents"]} for key, row in rows.items() if row["available_cents"]]
    elif not selection:
        raise OperationError("LINES_REQUIRED", "Selecione o consumo.", 400)
    result, seen = [], set()
    for line in selection:
        key = str(line["charge_id"])
        row = rows.get(key)
        if key in seen or not row or row["blocker"]:
            raise OperationError("LINE_NOT_TRANSFERABLE", "Consumo indisponível para transferência.")
        seen.add(key)
        quantity = line.get("quantity")
        amount = line.get("amount_cents")
        if quantity is not None:
            if type(quantity) is not int or quantity <= 0 or row["unit_price_cents"] <= 0:
                raise OperationError("INVALID_QUANTITY", "Quantidade inválida.", 400)
            quantity_amount = quantity * row["unit_price_cents"]
            if amount is not None and amount != quantity_amount:
                raise OperationError("QUANTITY_AMOUNT_MISMATCH", "Valor não corresponde à quantidade.", 400)
            amount = quantity_amount
        if type(amount) is not int or amount <= 0:
            raise OperationError("INVALID_AMOUNT", "Informe valor inteiro em centavos.", 400)
        if amount > row["available_cents"]:
            raise OperationError("INSUFFICIENT_TRANSFERABLE_BALANCE", "Saldo transferível insuficiente.", details={"current": transferability(source)})
        result.append({**row, "amount_cents": amount, "quantity": quantity})
    amount = sum(row["amount_cents"] for row in result)
    source_balance = totals(source)["exposure_cents"]
    if amount > source_balance:
        raise OperationError("INSUFFICIENT_TRANSFERABLE_BALANCE", "Saldo transferível insuficiente.")
    if destination:
        position = financial_position(destination)
    else:
        from modules.house_account.services import snapshot
        position = {"exposure_cents": 0, "effective_limit_cents": snapshot(source.venue_id)["operating_limit_cents"]}
    destination_balance = position["exposure_cents"] + amount
    if destination_balance > position["effective_limit_cents"]:
        raise OperationError("SPENDING_LIMIT_EXCEEDED", "Destino excede o limite. Solicite autorização de limite primeiro.")
    return {"lines": result, "amount_cents": amount, "source_after_cents": source_balance - amount,
            "destination_after_cents": destination_balance}


def capability(kind):
    return {"MOVE_LOCATION": Capability.TAB_MOVE, "CANCEL_EMPTY": Capability.TAB_CANCEL,
            "REOPEN": Capability.TAB_REOPEN}.get(kind, Capability.TAB_TRANSFER)


def locked_tabs(source_id, destination_id, actor):
    ids = {str(source_id)}
    if destination_id:
        ids.add(str(destination_id))
        if str(destination_id) == str(source_id):
            raise OperationError("SAME_TAB", "Escolha outra comanda.", 400)
    tabs = list(Tab.objects.select_for_update().filter(id__in=ids, venue_id=actor.venue_id).order_by("id"))
    if len(tabs) != len(ids):
        raise OperationError("TAB_NOT_FOUND", "Comanda não encontrada neste estabelecimento.", 404)
    by_id = {str(tab.id): tab for tab in tabs}
    return by_id[str(source_id)], by_id.get(str(destination_id))


@transaction.atomic
def preview(*, tab_id, data, actor):
    authorize(actor, capability(data["kind"]))
    source, destination = locked_tabs(tab_id, data.get("destination_tab_id"), actor)
    check_version(source, data["expected_version"])
    if destination:
        check_version(destination, data.get("destination_version"))
    if data["kind"] == "MERGE" and not destination:
        raise OperationError("DESTINATION_REQUIRED", "Escolha a comanda sobrevivente.", 400)
    return {"source": tab_payload(source), "destination": tab_payload(destination) if destination else None,
            **selected_lines(source, destination, data)}


def emit(actor, kind, source, metadata, reason=""):
    # Durable integration contract, consumed by timeline/invalidation projections.
    record_audit_event(actor=actor, event_type=kind, entity_type="Tab", entity_id=str(source.id),
                       reason=reason, metadata={**metadata, "invalidate": ["tabs", "guest_balance", "dispatch", "management"]})




def revoke(tab, reason):
    tab.guest_sessions.filter(revoked_at__isnull=True).update(revoked_at=timezone.now(), revoked_reason=reason)


@transaction.atomic
def execute(*, tab_id, data, actor):
    kind = data["kind"]
    authorize(actor, capability(kind))
    # Hospitality commands lock Table/Occupancy before Tab. Match that order.
    if kind == "MOVE_LOCATION" and data.get("occupancy_id"):
        from modules.hospitality.models import Table, TableOccupancy
        reference = TableOccupancy.objects.filter(pk=data["occupancy_id"], table__venue_id=actor.venue_id).values_list("table_id", flat=True).first()
        if reference:
            Table.objects.select_for_update().get(pk=reference)
            TableOccupancy.objects.select_for_update().get(pk=data["occupancy_id"])
    source, destination = locked_tabs(tab_id, data.get("destination_tab_id"), actor)
    key = data.get("idempotency_key", "")
    if not key or len(key) > 120:
        raise OperationError("IDEMPOTENCY_KEY_REQUIRED", "Chave da operação obrigatória.", 400)
    fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
    previous = source.operations.filter(idempotency_key=key).first()
    if previous:
        if previous.request_fingerprint != fingerprint:
            raise OperationError("IDEMPOTENCY_CONFLICT", "Chave já usada em outra operação.")
        return previous.response
    check_version(source, data["expected_version"])
    if destination:
        check_version(destination, data.get("destination_version"))
    operation = TabOperation.objects.create(source_tab=source, idempotency_key=key,
                    request_fingerprint=fingerprint, kind=kind, created_by_id=actor.staff_id)
    reason = data.get("reason", "").strip()
    result = {}
    if kind in FINANCIAL:
        if kind == "MERGE" and not destination:
            raise OperationError("DESTINATION_REQUIRED", "Escolha a comanda sobrevivente.", 400)
        result = selected_lines(source, destination, data)
        if not destination:
            from modules.ordering.services import open_tab
            destination = open_tab(actor=actor, display_label=data.get("destination_label", ""))
        transfer = TabTransfer.objects.create(operation=operation, venue_id=actor.venue_id, source_tab=source,
            destination_tab=destination, kind=kind, reason=reason, source_version=source.version, destination_version=destination.version)
        for line in result["lines"]:
            TabTransferLine.objects.create(transfer=transfer, source_charge_id=line["charge_id"], amount_cents=line["amount_cents"], quantity=line["quantity"])
        result["transfer_id"] = str(transfer.id)
        if kind == "MERGE":
            source.state, source.cancel_reason, source.merged_into = TabState.CANCELLED, "MERGED_INTO", destination
            source.save(update_fields=["state", "cancel_reason", "merged_into"])
            revoke(source, "MERGED_INTO")
        destination.version += 1
        destination.save(update_fields=["version"])
        sync_attention(source, actor)
        sync_attention(destination, actor)
        emit(actor, "tab.transfer_committed", source, {"destination_tab_id": str(destination.id), **result}, reason)
        emit(actor, {"MERGE": "tab.merged", "SPLIT": "tab.split", "MOVE_ITEMS": "tab.consumption_transferred"}[kind], source,
             {"destination_tab_id": str(destination.id), "transfer_id": str(transfer.id), "amount_cents": result["amount_cents"]}, reason)
    elif kind == "MOVE_LOCATION":
        check_open(source)
        from modules.hospitality.models import Table, TableOccupancy, TabOccupancyAssignment
        occupancy_id, point_id = data.get("occupancy_id"), data.get("service_point_id")
        if occupancy_id and point_id:
            raise OperationError("INVALID_LOCATION", "Escolha mesa ou ponto de atendimento.", 400)
        occupancy, point = None, None
        if occupancy_id:
            table_id = TableOccupancy.objects.filter(pk=occupancy_id, table__venue_id=actor.venue_id).values_list("table_id", flat=True).first()
            if table_id:
                Table.objects.select_for_update().get(pk=table_id)
                occupancy = TableOccupancy.objects.select_for_update().filter(pk=occupancy_id, released_at__isnull=True, table__status="OCCUPIED").first()
            if not occupancy:
                raise OperationError("OCCUPANCY_NOT_ACTIVE", "Ocupação não está ativa.")
        if point_id:
            point = ServicePoint.objects.select_for_update().filter(pk=point_id, venue_id=actor.venue_id, is_active=True).first()
            if not point:
                raise OperationError("SERVICE_POINT_NOT_FOUND", "Ponto de atendimento indisponível.", 404)
        before = tab_payload(source)
        source.occupancy_assignments.filter(released_at__isnull=True).update(released_at=timezone.now())
        if occupancy:
            TabOccupancyAssignment.objects.create(tab=source, occupancy=occupancy, assigned_by_id=actor.staff_id)
        source.service_point = point
        source.save(update_fields=["service_point"])
        from modules.dispatch.services import refresh_tab_destination
        refresh_tab_destination(source, actor)
        emit(actor, "tab.location_changed", source, {"before": before, "occupancy_id": str(occupancy_id) if occupancy_id else None, "service_point_id": str(point_id) if point_id else None})
    elif kind == "CANCEL_EMPTY":
        check_open(source)
        from modules.access.models import StaffSession
        from modules.access.capabilities import has_capability
        membership = StaffSession.objects.get(pk=actor.session_id).membership
        if source.opened_by_id != actor.staff_id and not has_capability(membership, Capability.TAB_TRANSFER):
            raise OperationError("OWN_TAB_REQUIRED", "Só pode cancelar sua própria comanda vazia.", 403)
        if source.orders.exists() or source.charges.exists() or source.payments.exists() or source.ledger_adjustments.exclude(amount_cents=0).exists() or source.incoming_transfers.exists() or source.outgoing_transfers.exists():
            raise OperationError("TAB_NOT_EMPTY", "Comanda possui histórico. Use o fluxo de correção.")
        source.state, source.cancel_reason = TabState.CANCELLED, reason or "ACCIDENTAL_OPEN"
        source.save(update_fields=["state", "cancel_reason"])
        revoke(source, "CANCELLED")
        emit(actor, "tab.cancelled", source, {}, source.cancel_reason)
    elif kind == "REOPEN":
        if source.state != TabState.CLOSED:
            raise OperationError("TAB_NOT_CLOSED", "Só comandas fechadas podem ser reabertas.")
        if not reason:
            raise OperationError("REASON_REQUIRED", "Informe o motivo para reabrir.", 400)
        blocker = payment_blocker(source, confirmed=False)
        if blocker:
            raise OperationError(*blocker)
        closed_at = source.closed_at.isoformat() if source.closed_at else None
        source.state = TabState.OPEN
        source.save(update_fields=["state"])
        sync_attention(source, actor)
        emit(actor, "tab.reopened", source, {"reopened_from_closed_at": closed_at}, reason)
        emit(actor, "tab.post_close_exception", source, {"original_closed_at": closed_at, "exposure_cents": totals(source)["exposure_cents"]}, reason)
    else:
        raise OperationError("INVALID_OPERATION", "Operação inválida.", 400)
    source.version += 1
    source.save(update_fields=["version"])
    response = {"operation_id": str(operation.id), "source": tab_payload(source),
                "destination": tab_payload(destination) if destination else None, **result}
    from django.core.serializers.json import DjangoJSONEncoder
    response = json.loads(json.dumps(response, cls=DjangoJSONEncoder))
    operation.response = response
    operation.save(update_fields=["response"])
    return response
