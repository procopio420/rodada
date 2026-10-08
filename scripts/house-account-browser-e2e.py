"""Real mobile Web proof; run against a disposable, seed_demo'd local database.

Start API on :8012 and Web on :3012 pointing to that API. Requires Python
Playwright and its Chromium browser. No API interception or response mocks.
"""
import os
import re
import uuid
from urllib.parse import urlparse

from playwright.sync_api import expect, sync_playwright

web_url = os.environ.get("HOUSE_PROOF_WEB_URL", "http://127.0.0.1:3012")
assert urlparse(web_url).hostname in {"127.0.0.1", "localhost"}, "Use a disposable local environment"

with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    manager = browser.new_context(base_url=web_url, viewport={"width": 390, "height": 844})
    guest = browser.new_context(base_url=web_url, viewport={"width": 390, "height": 844})

    def api(path, data=None, method="POST"):
        response = manager.request.fetch(path, method=method, data=data)
        assert response.ok, f"{path}: HTTP {response.status}: {response.text()}"
        return response.json()

    api("/api/auth/login", {"venue_slug": "bar-do-aderlan", "login_identifier": "ana",
                          "pin": "0420", "installation_id": "house-browser-" + str(uuid.uuid4()),
                          "platform": "WEB"})
    api("/api/auth/reauthenticate", {"pin": "0420"})
    products = api("/api/pos/catalog/products/", method="GET")["results"]
    product = next(p for p in products if p["active"] and p["availability"] == "AVAILABLE")
    price = product["price_cents"]
    api("/api/pos/house-account/policies/", {"kind": "VISITOR", "limit_cents": price * 2}, "PUT")
    table = api("/api/pos/hospitality/tables/", {"label": "Proof " + uuid.uuid4().hex[:8],
                                              "guest_ordering_mode": "DIRECT"})
    label = "Conta browser " + uuid.uuid4().hex[:8]
    guest_page = guest.new_page()
    guest_page.goto("/guest/" + table["public_token"])
    guest_page.get_by_label("Seu nome ou apelido (opcional)").fill(label)
    guest_page.get_by_role("button", name="Abrir minha comanda").click()
    product_button = guest_page.locator(".guestProduct").filter(has_text=product["name"])
    product_button.click()
    product_button.click()
    guest_page.get_by_role("button", name=re.compile("^Enviar ·")).click()
    expect(guest_page.get_by_text("Para continuar consumindo, peça ajuda à equipe.", exact=False)).to_be_visible()
    assert guest_page.get_by_role("button", name=re.compile("^Enviar ·")).is_disabled()
    assert guest_page.get_by_text("Aprovar limite temporário", exact=True).count() == 0

    tab = next(t for t in api("/api/pos/tabs/", method="GET")["results"] if t["display_label"] == label)
    manager_page = manager.new_page()
    manager_page.goto("/manage")
    house = manager_page.get_by_role("region", name="Conta da casa")
    expect(house.get_by_text("Limite de consumo atingido", exact=False).first).to_be_visible()
    house.get_by_label("Inspecionar comanda").select_option(tab["id"])
    house.get_by_label("Novo limite total (centavos)").fill(str(price * 4))
    house.get_by_label("Motivo", exact=True).fill("Aprovação operacional browser")
    house.get_by_label("Seu PIN de aprovação").fill("0420")
    house.get_by_role("button", name="Aprovar limite temporário", exact=True).click()
    expect(house.get_by_text("Limite temporário aprovado", exact=True)).to_be_visible()

    guest_page.get_by_role("button", name="Atualizar comanda").click()
    expect(guest_page.get_by_text("Para continuar consumindo, peça ajuda à equipe.", exact=False)).to_have_count(0)
    product_button.click()
    guest_page.get_by_role("button", name=re.compile("^Enviar ·")).click()
    expect(guest_page.get_by_text("Seu carrinho está vazio", exact=True)).to_be_visible()
    position = api(f"/api/pos/tabs/{tab['id']}/", method="GET")
    assert position["exposure_cents"] == price * 3

    guest.set_offline(True)
    expect(guest_page.get_by_text("Dados desatualizados.", exact=False)).to_be_visible()
    guest.set_offline(False)
    expect(guest_page.get_by_text("Dados desatualizados.", exact=False)).to_have_count(0)
    assert guest_page.locator("body").evaluate("el => el.scrollWidth <= window.innerWidth")
    assert manager_page.locator("body").evaluate("el => el.scrollWidth <= window.innerWidth")

    api(f"/api/pos/tabs/{tab['id']}/payments/", {"amount_cents": price * 3,
        "method": "EXTERNAL_TERMINAL", "idempotency_key": uuid.uuid4().hex})
    closed = api(f"/api/pos/tabs/{tab['id']}/close/", {})
    assert closed["state"] == "CLOSED"
    print("PASS: Guest Web → Hit limit → Gerência approval → Continue → Reconnect → Pay → Close")
    browser.close()
