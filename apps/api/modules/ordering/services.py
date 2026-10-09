import hashlib
import json
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from modules.access.context import ActorContext
from modules.audit.services import record_audit_event
from modules.catalog.models import AvailabilityState, Product, ProductAvailability
from modules.ordering.models import Order, OrderItem, OrderItemState, OrderSource, Tab, TabState


@dataclass(frozen=True)
class OrderingServiceError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: dict | None = None


@transaction.atomic
def open_tab(
    *,
    actor: ActorContext,
    display_label: str = "",
    customer_id=None,
) -> Tab:
    from modules.house_account.services import snapshot, sync_attention
    tab = Tab.objects.create(
        venue_id=actor.venue_id,
        display_label=display_label.strip(),
        opened_by_id=actor.staff_id,
        **snapshot(actor.venue_id, customer_id),
    )
    sync_attention(tab, actor)
    record_audit_event(
        actor=actor,
        event_type="tab.opened",
        entity_type="Tab",
        entity_id=str(tab.id),
        metadata={"display_label": tab.display_label},
    )
    return tab


@transaction.atomic
def confirm_order(
    *,
    tab_id,
    source: str,
    lines: list[dict],
    actor: ActorContext | None = None,
    idempotency_key: str = "",
) -> Order:
    if source not in OrderSource.values:
        raise OrderingServiceError("INVALID_ORDER_SOURCE", "Origem do pedido inválida.", 400)
    if not lines:
        raise OrderingServiceError("EMPTY_ORDER", "Pedido precisa ter ao menos um item.", 400)

    tab = (
        Tab.objects.select_for_update(of=("self",))
        .select_related("venue")
        .filter(pk=tab_id)
        .first()
    )
    if not tab:
        raise OrderingServiceError("TAB_NOT_FOUND", "Comanda não encontrada.", 404)
    if actor is not None and actor.venue_id != tab.venue_id:
        raise OrderingServiceError("TAB_NOT_FOUND", "Comanda não encontrada.", 404)
    normalized_lines = []
    product_ids = []
    for line in lines:
        product_id = line.get("product_id")
        quantity = line.get("quantity")
        if not product_id or not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
            raise OrderingServiceError(
                "INVALID_ORDER_LINE",
                "Cada item precisa de product_id e quantity positiva.",
                400,
            )
        normalized_lines.append(line)
        product_ids.append(product_id)

    request_fingerprint = _order_fingerprint(source=source, lines=normalized_lines)
    if idempotency_key:
        existing = Order.objects.filter(tab=tab, idempotency_key=idempotency_key).first()
        if existing:
            if existing.request_fingerprint != request_fingerprint:
                raise OrderingServiceError(
                    "IDEMPOTENCY_CONFLICT",
                    "A chave já foi usada para outro pedido.",
                    409,
                )
            # The tab row is locked above, so a second request cannot race past
            # this point and create a second order or financial effect.
            existing._idempotency_replay = True
            return existing

    if tab.state not in (TabState.OPEN, TabState.REQUIRES_ACTION):
        raise OrderingServiceError("TAB_NOT_OPEN", "Esta comanda não aceita novos pedidos.", 409,
                                   {"state": tab.state})

    locked_products = {
        product.id: product
        for product in Product.objects.select_for_update().filter(
            id__in=product_ids,
            venue_id=tab.venue_id,
        ).order_by("id")
    }
    locked_availability = {
        availability.product_id: availability
        for availability in ProductAvailability.objects.select_for_update().filter(
            product_id__in=locked_products.keys()
        )
    }

    invalid_products = []
    for line in normalized_lines:
        product_id = line["product_id"]
        product = locked_products.get(product_id)
        if product is None:
            invalid_products.append(
                {"product_id": str(product_id), "reason": "NOT_FOUND_OR_OTHER_VENUE"}
            )
            continue
        if not product.active:
            invalid_products.append(
                {"product_id": str(product.id), "reason": "INACTIVE"}
            )
            continue
        availability = locked_availability.get(product.id)
        if availability is None or availability.state != AvailabilityState.AVAILABLE:
            invalid_products.append(
                {"product_id": str(product.id), "reason": "UNAVAILABLE"}
            )

    if invalid_products:
        raise OrderingServiceError(
            "PRODUCTS_NOT_CONFIRMABLE",
            "Um ou mais itens não podem mais ser confirmados.",
            409,
            {"products": invalid_products},
        )

    from modules.house_account.services import financial_position, sync_attention
    position = financial_position(tab)
    from modules.catalog.customization import price_customization
    snapshots = [price_customization(locked_products[line["product_id"]], line) for line in normalized_lines]
    order_total = sum(snapshot["line_total_cents"] for snapshot in snapshots)
    if position["exposure_cents"] + order_total > position["effective_limit_cents"]:
        raise OrderingServiceError("SPENDING_LIMIT_EXCEEDED",
            "Consumo acima do limite. Receba um pagamento parcial ou solicite aprovação da gerência.",
            409, {**position, "requested_cents": order_total})

    order = Order.objects.create(
        tab=tab,
        source=source,
        confirmed_by_id=actor.staff_id if actor else None,
        idempotency_key=idempotency_key,
        request_fingerprint=request_fingerprint if idempotency_key else "",
    )
    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                product_id=snapshot["product_id"],
                product_name_snapshot=snapshot["product_name"],
                unit_price_cents=snapshot["unit_price_cents"],
                quantity=snapshot["quantity"],
                customization_snapshot=snapshot,
                fulfillment_station_snapshot=snapshot["fulfillment_station"],
            )
            for snapshot in snapshots
        ]
    )

    tab.version += 1
    tab.save(update_fields=["version"])

    if actor is not None:
        record_audit_event(
            actor=actor,
            event_type="order.confirmed",
            entity_type="Order",
            entity_id=str(order.id),
            metadata={
                "tab_id": str(tab.id),
                "source": source,
                "item_count": len(normalized_lines),
                "tab_version": tab.version,
            },
        )

    # The financial effect is derived from the confirmed snapshots, never from
    # a mutable catalog price. One-to-one Charge makes retries exactly-once.
    from modules.ledger.services import create_charges_for_order
    create_charges_for_order(order, actor)
    from modules.realtime.services import emit_event
    emit_event(venue_id=tab.venue_id, event_type="order.confirmed", aggregate_type="Order",
               aggregate_id=order.id, tab_id=tab.id)
    sync_attention(tab, actor)

    return order


def _order_fingerprint(*, source: str, lines: list[dict]) -> str:
    """Aggregate identical configurations; preserve variant, choices and note intent."""
    # Preserve the already-deployed fingerprint for simple-product requests.
    # Encrypted pre-upgrade intents must still replay confirmed Orders exactly once.
    if all(not line.get("variant_id") and not line.get("modifier_option_ids")
           and not line.get("special_instructions") for line in lines):
        quantities = {}
        for line in lines:
            key = str(line["product_id"])
            quantities[key] = quantities.get(key, 0) + line["quantity"]
        payload = {"source": source, "lines": sorted(quantities.items())}
        return hashlib.sha256(json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
    quantities = {}
    for line in lines:
        configuration = json.dumps({"product_id": str(line["product_id"]),
            "variant_id": str(line.get("variant_id")) if line.get("variant_id") else None,
            "modifier_option_ids": sorted(str(i) for i in line.get("modifier_option_ids", [])),
            "special_instructions": line.get("special_instructions", "")}, sort_keys=True)
        quantities[configuration] = quantities.get(configuration, 0) + line["quantity"]
    return hashlib.sha256(json.dumps({"source": source, "lines": sorted(quantities.items())},
                                    separators=(",", ":")).encode()).hexdigest()


_TRANSITIONS = {
    "NEW": {"ACCEPTED"},
    "ACCEPTED": {"PREPARING", "READY"},
    "PREPARING": {"READY"},
    "READY": {"PICKED_UP", "DELIVERED"},
    "PICKED_UP": {"DELIVERED"},
}
_TIMESTAMP_FIELDS = {
    "ACCEPTED": "accepted_at", "PREPARING": "preparing_at", "READY": "ready_at",
    "PICKED_UP": "picked_up_at", "DELIVERED": "delivered_at",
}


@transaction.atomic
def transition_order_item(*, item_id, target_state, actor):
    item = OrderItem.objects.select_for_update().select_related("order__tab").filter(pk=item_id, order__tab__venue_id=actor.venue_id).first()
    if not item:
        raise OrderingServiceError("ORDER_ITEM_NOT_FOUND", "Item não encontrado.", 404)
    # Financial closure must not strand already-confirmed production. These
    # transitions never create consumption or change the closed Tab's ledger.
    if target_state not in _TRANSITIONS.get(item.state, set()):
        raise OrderingServiceError("INVALID_ITEM_TRANSITION", "Transição operacional inválida.", 409)
    item.state = target_state
    setattr(item, _TIMESTAMP_FIELDS[target_state], timezone.now())
    item.save(update_fields=["state", _TIMESTAMP_FIELDS[target_state]])
    record_audit_event(actor=actor, event_type="order_item.transitioned", entity_type="OrderItem", entity_id=str(item.id), metadata={"state": target_state})
    if target_state == OrderItemState.READY:
        # Dispatch is derived from canonical per-item readiness.  It is safe to
        # replay and remains inside this transaction, so a READY item cannot
        # commit without its corresponding delivery work.
        from modules.dispatch.services import ensure_delivery_task_for_ready_order_item

        ensure_delivery_task_for_ready_order_item(item_id=item.id, actor=actor)
    return item
