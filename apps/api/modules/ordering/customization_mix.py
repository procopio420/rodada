"""Internal gross selection facts; Management owns authorization and business dates.

No mutable Catalog labels/prices, ledger calculations or persisted projections.
Cancelled originals remain gross facts; correction-generated children are not sales.
"""

from django.utils import timezone

from modules.ordering.models import OrderItem


def selection_mix(*, venue_id, start, end):
    """Aggregate snapshots in [start, end), weighted by OrderItem quantity.

    Rows retain label/price revisions instead of guessing a current catalog identity.
    selected_units/product_units are attach-rate inputs. Totals are gross snapshot
    cents, not net revenue, and never include payment/refund/discount calculations.
    """
    if timezone.is_naive(start) or timezone.is_naive(end) or start >= end:
        raise ValueError("Use a nonempty timezone-aware [start, end) interval")
    products, variants, modifiers = {}, {}, {}
    items = (
        OrderItem.objects.filter(
            order__tab__venue_id=venue_id,
            order__confirmed_at__gte=start,
            order__confirmed_at__lt=end,
            replacement_correction__isnull=True,
        )
        .order_by("id")
        .values(
            "product_id",
            "product_name_snapshot",
            "quantity",
            "state",
            "unit_price_cents",
            "customization_snapshot",
        )
    )
    for item in items.iterator():
        product_id = str(item["product_id"])
        product_name = item["product_name_snapshot"]
        quantity = item["quantity"]
        cancelled = quantity if item["state"] == "CANCELLED" else 0
        product = products.setdefault(
            product_id,
            {
                "product_id": product_id,
                "confirmed_units": 0,
                "cancelled_units": 0,
                "customized_units": 0,
                "modifier_attached_units": 0,
            },
        )
        product["confirmed_units"] += quantity
        product["cancelled_units"] += cancelled
        snapshot = item["customization_snapshot"] or {}
        variant = snapshot.get("variant")
        options = snapshot.get("modifiers", [])
        if variant or options:
            product["customized_units"] += quantity
        if options:
            product["modifier_attached_units"] += quantity
        variant_id = variant["id"] if variant else None
        variant_name = variant["name"] if variant else ""
        base = (
            variant["price_cents"]
            if variant
            else snapshot.get("base_price_cents", item["unit_price_cents"])
        )
        key = (product_id, product_name, variant_id or "", variant_name, base)
        row = variants.setdefault(
            key,
            {
                "product_id": product_id,
                "product_name": product_name,
                "variant_id": variant_id,
                "variant_name": variant_name,
                "base_price_cents": base,
                "selected_units": 0,
                "cancelled_units": 0,
                "base_total_cents": 0,
            },
        )
        row["selected_units"] += quantity
        row["cancelled_units"] += cancelled
        row["base_total_cents"] += base * quantity
        for option in options:
            key = (
                product_id,
                product_name,
                option["group_id"],
                option["group_name"],
                option["option_id"],
                option["name"],
                option["price_delta_cents"],
                option["semantic_kind"],
            )
            row = modifiers.setdefault(
                key,
                {
                    "product_id": product_id,
                    "product_name": product_name,
                    "group_id": option["group_id"],
                    "group_name": option["group_name"],
                    "option_id": option["option_id"],
                    "option_name": option["name"],
                    "semantic_kind": option["semantic_kind"],
                    "price_delta_cents": option["price_delta_cents"],
                    "selected_units": 0,
                    "cancelled_units": 0,
                    "delta_total_cents": 0,
                },
            )
            row["selected_units"] += quantity
            row["cancelled_units"] += cancelled
            row["delta_total_cents"] += option["price_delta_cents"] * quantity
    return {
        "venue_id": str(venue_id),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "basis": "GROSS_CONFIRMED_SELECTIONS",
        "products": [products[key] for key in sorted(products)],
        "variants": [variants[key] for key in sorted(variants)],
        "modifiers": [
            {**modifiers[key], "product_units": products[key[0]]["confirmed_units"]}
            for key in sorted(modifiers)
        ],
    }
