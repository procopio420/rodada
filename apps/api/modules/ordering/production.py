"""Canonical production commands; configuration never comes from today's catalog."""
import hashlib
import json

from django.db import transaction

from modules.access.capabilities import Capability, has_capability
from modules.access.models import StaffSession
from modules.audit.services import record_audit_event
from modules.ordering.models import OrderItem, ProductionBatch, Tab
from modules.ordering.services import OrderingServiceError, is_instant_pickup, transition_order_item


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def snapshot_fingerprint(snapshot):
    return hashlib.sha256(canonical(snapshot).encode()).hexdigest()


def configuration(item, station):
    snapshot = item.customization_snapshot
    def identified(value):
        return isinstance(value, str) and bool(value)
    if (not isinstance(snapshot, dict) or snapshot.get("product_id") != str(item.product_id)
            or snapshot.get("fulfillment_station") != station or "variant" not in snapshot
            or not isinstance(snapshot.get("modifiers"), list)
            or not isinstance(snapshot.get("special_instructions"), str)):
        return None
    variant = snapshot["variant"]
    if variant is not None and (not isinstance(variant, dict)
            or not identified(variant.get("id")) or not identified(variant.get("name"))):
        return None
    modifiers = snapshot["modifiers"]
    fields = ("option_id", "group_id", "name", "group_name", "semantic_kind")
    if any(not isinstance(option, dict) or any(not identified(option.get(key)) for key in fields)
           for option in modifiers):
        return None
    result = {key: value for key, value in snapshot.items()
              if key not in ("base_price_cents", "unit_price_cents", "quantity", "line_total_cents")}
    result["variant"] = ({key: value for key, value in variant.items()
                          if key not in ("price_cents", "price_delta_cents")} if variant else None)
    result["modifiers"] = sorted(canonical({key: value for key, value in option.items()
                                           if key != "price_delta_cents"}) for option in modifiers)
    result["product_name"] = item.product_name_snapshot
    return canonical(result)


@transaction.atomic
def execute_production_batch(*, actor, idempotency_key, station, target_state, lines):
    # NO KEY UPDATE serializes keys without blocking audit FK checks from
    # Tab-first correction transactions in this same session.
    session = StaffSession.objects.select_for_update(of=("self",), no_key=True).select_related(
        "staff_member", "membership", "device",
    ).filter(pk=actor.session_id, venue_id=actor.venue_id, staff_member_id=actor.staff_id).first()
    if session is None or not session.is_valid:
        raise OrderingServiceError("SESSION_INVALID", "Sessão original indisponível.", 403)
    if not has_capability(session.membership, Capability.ORDER_CONFIRM):
        raise OrderingServiceError("CAPABILITY_REQUIRED", "Sem autorização para produção.", 403)
    # Sorting makes selection order irrelevant while preserving all preconditions.
    lines = sorted([{**line, "item_id": str(line["item_id"])} for line in lines],
                   key=lambda line: line["item_id"])
    payload = {"station": station, "target_state": target_state, "lines": lines}
    fingerprint = snapshot_fingerprint(payload)
    previous = ProductionBatch.objects.filter(
        venue_id=actor.venue_id, session=session, idempotency_key=idempotency_key,
    ).first()
    if previous:
        if previous.request_fingerprint != fingerprint:
            raise OrderingServiceError("IDEMPOTENCY_CONFLICT", "Chave usada para outro lote.", 409)
        return previous.receipt

    ids = [line["item_id"] for line in lines]
    scoped = OrderItem.objects.filter(pk__in=ids, order__tab__venue_id=actor.venue_id)
    tab_ids = scoped.values_list("order__tab_id", flat=True).distinct()
    list(Tab.objects.select_for_update().filter(pk__in=tab_ids).order_by("id"))
    items = {str(item.id): item for item in scoped.select_for_update(of=("self",))
             .select_related("order").prefetch_related("corrections").order_by("id")}
    results = []
    signatures = set()
    for line in lines:
        item = items.get(line["item_id"])
        reasons = []
        if item is None:
            reasons.append("ITEM_NOT_FOUND")
        else:
            signature = configuration(item, station)
            if signature is None or item.fulfillment_station_snapshot != station:
                reasons.append("CONFIGURATION_NOT_VERIFIABLE")
            else:
                signatures.add(signature)
            origin_allowed = (
                (item.state in ("NEW", "ACCEPTED") and not is_instant_pickup(item))
                if target_state == "PREPARING" else
                (item.state == "PREPARING" or
                 (item.state in ("NEW", "ACCEPTED") and is_instant_pickup(item)))
            )
            if item.order.status != "CONFIRMED" or item.state != line["expected_state"] or not origin_allowed:
                reasons.append("STATE_CONFLICT")
            if item.remaining_quantity != line["quantity"]:
                reasons.append("QUANTITY_CONFLICT")
            if snapshot_fingerprint(item.customization_snapshot) != line["snapshot_fingerprint"]:
                reasons.append("SNAPSHOT_CONFLICT")
        results.append({"item_id": line["item_id"], "status": "NOT_APPLIED", "conflicts": reasons})
    if len(signatures) > 1:
        for result in results:
            result["conflicts"].append("CONFIGURATION_CONFLICT")
    rejected = any(result["conflicts"] for result in results)
    command = ProductionBatch.objects.create(
        venue_id=actor.venue_id, session=session, actor_id=actor.staff_id,
        idempotency_key=idempotency_key, request_fingerprint=fingerprint,
    )
    if not rejected:
        for result in results:
            transition_order_item(item_id=result["item_id"], target_state=target_state,
                                  actor=actor, command_id=command.id)
            result.update(status="APPLIED", state=target_state)
    receipt = {"command_id": str(command.id), "idempotency_key": idempotency_key,
               "station": station, "target_state": target_state,
               "status": "REJECTED" if rejected else "APPLIED", "lines": results}
    command.receipt = receipt
    command.save(update_fields=["receipt"])
    record_audit_event(actor=actor, event_type="production_batch.completed",
                       entity_type="ProductionBatch", entity_id=str(command.id),
                       metadata={**receipt, "quantity": sum(line["quantity"] for line in lines)})
    return receipt
