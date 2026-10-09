"""Canonical published schema and confirmation-time pricing. Caller holds Product locks."""

from modules.catalog.models import ProductModifierGroup, ProductVariant


def ordering_schema(product, *, include_inactive=False):
    variants = product.variants.all()
    links = product.modifier_links.all()
    return {
        "variants": [
            {
                "id": str(v.id),
                "name": v.name,
                "price_cents": v.price_cents,
                "active": v.active,
                "is_default": v.is_default,
                "sort_order": v.sort_order,
                "availability": v.availability,
                "version": v.version,
            }
            for v in variants
            if include_inactive or v.active
        ],
        "modifier_groups": [
            {
                "id": str(link.group_id),
                "name": link.group.name,
                "active": link.group.active,
                "version": link.group.version,
                "selection_mode": link.group.selection_mode,
                "min_selections": link.group.min_selections,
                "max_selections": link.group.max_selections,
                "required": link.group.min_selections > 0,
                "sort_order": link.sort_order,
                "options": [
                    {
                        "id": str(o.id),
                        "name": o.name,
                        "price_delta_cents": o.price_delta_cents,
                        "semantic_kind": o.semantic_kind,
                        "active": o.active,
                        "default_selected": o.default_selected,
                        "sort_order": o.sort_order,
                        "availability": o.availability,
                        "version": o.version,
                    }
                    for o in link.group.options.all()
                    if include_inactive or o.active
                ],
            }
            for link in links
            if include_inactive or link.group.active
        ],
    }


def price_customization(product, line):
    from modules.ordering.services import OrderingServiceError

    def reject(code, message, **details):
        raise OrderingServiceError(code, message, 409, {"product_id": str(product.id), **details})

    variants = list(ProductVariant.objects.filter(product=product).order_by("sort_order", "id"))
    variant_id = line.get("variant_id")
    variant = next((v for v in variants if str(v.id) == str(variant_id)), None)
    if variant_id and (not variant or not variant.active or variant.availability != "AVAILABLE"):
        reject(
            "VARIANT_UNAVAILABLE",
            "Esta variação não está disponível. Revise o item.",
            variant_id=str(variant_id),
        )
    if any(v.active for v in variants) and not variant:
        reject("VARIANT_REQUIRED", "Escolha uma variação.")
    selected_ids = [str(i) for i in line.get("modifier_option_ids", [])]
    if len(selected_ids) != len(set(selected_ids)):
        reject("INVALID_MODIFIER_SELECTION", "Uma opção não pode ser repetida.")
    remaining = set(selected_ids)
    modifiers = []
    links = (
        ProductModifierGroup.objects.filter(product=product, group__active=True)
        .select_related("group")
        .prefetch_related("group__options")
        .order_by("sort_order", "id")
    )
    for link in links:
        group = link.group
        options = [o for o in group.options.all() if str(o.id) in remaining]
        for option in options:
            remaining.remove(str(option.id))
            if not option.active or option.availability != "AVAILABLE":
                reject(
                    "MODIFIER_UNAVAILABLE",
                    "Uma opção ficou indisponível. Revise o item.",
                    option_id=str(option.id),
                    group_id=str(group.id),
                )
        if len(options) < group.min_selections:
            reject("MODIFIER_REQUIRED", f"Complete {group.name}.", group_id=str(group.id))
        if len(options) > group.max_selections or (
            group.selection_mode == "SINGLE" and len(options) > 1
        ):
            reject(
                "TOO_MANY_MODIFIERS", f"Revise as escolhas de {group.name}.", group_id=str(group.id)
            )
        modifiers.extend(
            {
                "group_id": str(group.id),
                "group_name": group.name,
                "option_id": str(o.id),
                "name": o.name,
                "price_delta_cents": o.price_delta_cents,
                "semantic_kind": o.semantic_kind,
            }
            for o in options
        )
    if remaining:
        reject(
            "INVALID_MODIFIER_SELECTION",
            "Opção não pertence a este produto.",
            option_ids=sorted(remaining),
        )
    base = variant.price_cents if variant else product.price_cents
    total = base + sum(o["price_delta_cents"] for o in modifiers)
    if total > 2147483647 or total * line["quantity"] > 2147483647:
        reject("INVALID_ORDER_LINE", "Valor do item excede o máximo permitido.")
    return {
        "product_id": str(product.id),
        "product_name": product.name,
        "base_price_cents": product.price_cents,
        "variant": None
        if not variant
        else {
            "id": str(variant.id),
            "name": variant.name,
            "price_cents": variant.price_cents,
            "price_delta_cents": variant.price_cents - product.price_cents,
        },
        "modifiers": modifiers,
        "special_instructions": line.get("special_instructions", ""),
        "unit_price_cents": total,
        "quantity": line["quantity"],
        "line_total_cents": total * line["quantity"],
        "fulfillment_station": product.fulfillment_station,
    }
