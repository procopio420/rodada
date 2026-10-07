from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from modules.access.context import ActorContext
from modules.audit.services import record_audit_event
from modules.catalog.models import AvailabilityState, Product, ProductAvailability
from modules.ordering.models import Order, OrderItem, OrderSource, Tab, TabState


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
) -> Tab:
    tab = Tab.objects.create(
        venue_id=actor.venue_id,
        display_label=display_label.strip(),
        opened_by_id=actor.staff_id,
    )
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
) -> Order:
    if source not in OrderSource.values:
        raise OrderingServiceError("INVALID_ORDER_SOURCE", "Origem do pedido inválida.", 400)
    if not lines:
        raise OrderingServiceError("EMPTY_ORDER", "Pedido precisa ter ao menos um item.", 400)

    tab = (
        Tab.objects.select_for_update()
        .select_related("venue")
        .filter(pk=tab_id)
        .first()
    )
    if not tab:
        raise OrderingServiceError("TAB_NOT_FOUND", "Comanda não encontrada.", 404)
    if actor is not None and actor.venue_id != tab.venue_id:
        raise OrderingServiceError("TAB_NOT_FOUND", "Comanda não encontrada.", 404)
    if tab.state not in (TabState.OPEN, TabState.REQUIRES_ACTION):
        raise OrderingServiceError(
            "TAB_NOT_OPEN",
            "Esta comanda não aceita novos pedidos.",
            409,
            {"state": tab.state},
        )

    normalized_lines: list[tuple[object, int]] = []
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
        normalized_lines.append((product_id, quantity))
        product_ids.append(product_id)

    locked_products = {
        product.id: product
        for product in Product.objects.select_for_update().filter(
            id__in=product_ids,
            venue_id=tab.venue_id,
        )
    }
    locked_availability = {
        availability.product_id: availability
        for availability in ProductAvailability.objects.select_for_update().filter(
            product_id__in=locked_products.keys()
        )
    }

    invalid_products = []
    for product_id, _quantity in normalized_lines:
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

    order = Order.objects.create(
        tab=tab,
        source=source,
        confirmed_by_id=actor.staff_id if actor else None,
    )
    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                product=locked_products[product_id],
                product_name_snapshot=locked_products[product_id].name,
                unit_price_cents=locked_products[product_id].price_cents,
                quantity=quantity,
            )
            for product_id, quantity in normalized_lines
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

    return order
