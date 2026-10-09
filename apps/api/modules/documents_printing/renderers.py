"""Versioned deterministic output, escaped for HTML and stripped of printer controls."""

import html
import json
import textwrap
import unicodedata

TITLES = {
    "CUSTOMER_CHECK": "CONTA",
    "PAYMENT_RECEIPT": "RECIBO DE PAGAMENTO",
    "PARTIAL_PAYMENT_RECEIPT": "RECIBO DE PAGAMENTO PARCIAL",
    "CLOSED_TAB_RECEIPT": "COMANDA ENCERRADA",
    "PRODUCTION_TICKET": "PRODUÇÃO",
}


METHODS = {
    "CASH": "Dinheiro",
    "EXTERNAL_TERMINAL": "Maquininha externa",
    "TAP_TO_PAY": "Cartão por aproximação",
    "CARD_ONLINE": "Cartão online",
    "CARD": "Cartão",
    "PIX": "Pix",
    "OTHER": "Outro",
}
PAYMENT_STATES = {
    "CONFIRMED": "Confirmado",
    "PARTIALLY_REFUNDED": "Parcialmente estornado",
    "REFUNDED": "Estornado",
}
ADJUSTMENTS = {
    "ORDER_ITEM_CANCELLATION": "Cancelamento de item",
    "COURTESY_REPLACEMENT": "Cortesia de reposição",
}


def safe_text(value):
    return "".join(c for c in str(value) if not unicodedata.category(c).startswith("C"))


def money(cents):
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}R$ {cents // 100},{cents % 100:02d}"


def lines(document, reprint=False):
    data = document.snapshot
    result = [TITLES[document.kind], "DOCUMENTO NÃO FISCAL"]
    if reprint:
        result += ["*** REIMPRESSÃO / CÓPIA ***"]
    result += [
        data["venue"],
        f"Comanda: {data['tab_label']}",
        f"Documento: {document.id}",
        f"Conta gerada em: {data['generated_at']}",
        f"Dia operacional: {data['business_date']}",
    ]
    if document.station:
        result += [
            f"Estação: {'Bar' if document.station == 'BAR' else 'Cozinha'}",
            f"Pedido: {document.source_id}",
            f"Confirmado em: {data['confirmed_at']}",
            "FALLBACK — conferir fila digital",
        ]
    for item in data["items"]:
        result += [
            f"{item['quantity']} x {item['name']}"
            + (" (pedido original)" if item.get("allocated") else "")
        ]
        customization = item["customization"]
        variant = customization.get("variant")
        if variant:
            result += ["  " + str(variant.get("name", ""))]
        for modifier in customization.get("modifiers", []):
            prefix = (
                "Sem "
                if modifier.get("semantic_kind") == "REMOVE"
                else "+ "
                if modifier.get("semantic_kind") == "ADD"
                else ""
            )
            result += ["  " + prefix + str(modifier.get("name", ""))]
        if customization.get("special_instructions"):
            result += ["  Obs: " + str(customization["special_instructions"])]
        if document.kind != "PRODUCTION_TICKET":
            result += [
                f"  Unitário {money(item['unit_price_cents'])} · Total {money(item['total_cents'])}"
            ]
        if item.get("allocated"):
            result += [f"  Valor atribuído à comanda: {money(item['responsibility_cents'])}"]
    for transfer in data.get("transfers", []):
        direction = "Recebido" if transfer["incoming"] else "Transferido"
        quantity = f"{transfer['quantity']} x " if transfer["quantity"] is not None else "Parte de "
        result += [
            f"{direction}: {quantity}{transfer['product_name']} — {money(transfer['amount_cents'])}"
        ]
    if "totals" in data:
        labels = {
            "charges_cents": "Consumo",
            "adjustments_cents": "Ajustes",
            "transfers_cents": "Transferências",
            "payments_cents": "Pagamentos confirmados",
            "refunds_cents": "Estornos",
            "exposure_cents": "Saldo",
        }
        result += [f"{label}: {money(data['totals'][key])}" for key, label in labels.items()]
        result += [
            f"Ajuste {ADJUSTMENTS.get(a['kind'], 'Ajuste')}: {money(a['amount_cents'])}"
            for a in data["adjustments"]
        ]
        result += [
            f"Pagamento {p['id']} {METHODS.get(p['method'], 'Outro')}: {money(p['amount_cents'])} ({PAYMENT_STATES.get(p['status'], 'Não confirmado')}) em {p['confirmed_at']}"
            for p in data["payments"]
        ]
        result += [f"Estorno {r['id']}: {money(r['amount_cents'])}" for r in data["refunds"]]
    if data.get("payment"):
        p = data["payment"]
        result += [
            f"Pagamento confirmado: {money(p['amount_cents'])}",
            f"Método: {METHODS.get(p['method'], 'Outro')}",
            f"Referência: {p['id']}",
            f"Confirmado em: {p['confirmed_at']}",
            f"Estado: {PAYMENT_STATES.get(p['status'], 'Não confirmado')}",
        ]
    if any(p.get("simulated") for p in data.get("payments", [])):
        result += ["PAGAMENTO SIMULADO — SEM VALOR COMPROBATÓRIO"]
    return [safe_text(line) for line in result]


def render_text(document, width_mm=80, reprint=False):
    if width_mm not in (58, 80):
        raise ValueError("Unsupported paper width")
    columns = 32 if width_mm == 58 else 48
    return (
        "\n".join(
            part
            for line in lines(document, reprint)
            for part in (textwrap.wrap(line, columns) or [""])
        )
        + "\n"
    )


def render_html(document, width_mm=80, reprint=False):
    text = render_text(document, width_mm, reprint)
    content = html.escape(text)
    height_mm = max(50, min(297, 12 + len(text.splitlines()) * 4))
    return f'<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Recibo não fiscal</title><style>@page{{size:{width_mm}mm {height_mm}mm;margin:3mm}}body{{max-width:{width_mm - 6}mm;margin:0 auto;color:#000;background:#fff}}pre{{white-space:pre-wrap;font:12px monospace;overflow-wrap:anywhere}}@media print{{button{{display:none}}}}</style><button onclick="window.print()">Imprimir / Salvar PDF</button><pre>{content}</pre></html>'


def render_escpos(document, width_mm=80, reprint=False, cut=False):
    content = unicodedata.normalize("NFKD", render_text(document, width_mm, reprint)).encode(
        "ascii", "ignore"
    )
    return b"\x1b@" + content + b"\n\n\n" + (b"\x1dV\x00" if cut else b"")


def canonical_json(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
