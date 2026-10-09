from types import SimpleNamespace


def receipt_fixture(kind):
    data = {
        "venue": "Bar do Aderlan",
        "tab_label": "Balcão / Ana",
        "generated_at": "2026-10-09T20:00:00-03:00",
        "business_date": "2026-10-09",
        "confirmed_at": "2026-10-09T22:45:00+00:00",
        "items": [
            {
                "quantity": 2,
                "name": "Porção",
                "unit_price_cents": 1200,
                "total_cents": 2400,
                "customization": {
                    "variant": {"name": "Grande"},
                    "modifiers": [
                        {"name": "cebola", "semantic_kind": "REMOVE"},
                        {"name": "Queijo extra", "price_delta_cents": 200, "semantic_kind": "ADD"},
                    ],
                    "special_instructions": "Bem quente",
                },
            }
        ],
    }
    payment = {
        "id": "33333333-3333-4333-8333-333333333333",
        "method": "CASH",
        "amount_cents": 1000,
        "status": "CONFIRMED",
        "confirmed_at": "2026-10-09T23:00:00+00:00",
    }
    if kind != "PRODUCTION_TICKET":
        data.update(
            totals={
                "charges_cents": 2400,
                "adjustments_cents": -200,
                "transfers_cents": 0,
                "payments_cents": 1000,
                "refunds_cents": 0,
                "exposure_cents": 1200,
            },
            payments=[payment],
            refunds=[],
            adjustments=[{"kind": "ORDER_ITEM_CANCELLATION", "amount_cents": -200}],
        )
    if kind in ("PAYMENT_RECEIPT", "PARTIAL_PAYMENT_RECEIPT"):
        data["payment"] = payment
    return SimpleNamespace(
        id="11111111-1111-4111-8111-111111111111",
        source_id="22222222-2222-4222-8222-222222222222",
        kind=kind,
        station="KITCHEN" if kind == "PRODUCTION_TICKET" else "",
        snapshot=data,
    )
