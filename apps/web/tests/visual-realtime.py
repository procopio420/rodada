"""Real browser + ASGI smoke against a disposable PostgreSQL database.
POSTGRES_DB=rodada_realtime_verification python apps/web/tests/visual-realtime.py
Requires API on 18764, built Web on 18765, and playwright Chromium.
"""
import json, os, sys, time, uuid, subprocess, re
from pathlib import Path
from urllib.request import Request, urlopen
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "api"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django
django.setup()
from modules.venue.models import Venue
from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.catalog.models import Product
from modules.hospitality.models import Table, GuestOrderingMode
def dispatch_pending():
    subprocess.run([sys.executable, "manage.py", "dispatch_realtime", "--once"], cwd=Path(__file__).resolve().parents[2] / "api", check=True, capture_output=True)
from playwright.sync_api import sync_playwright
suffix = uuid.uuid4().hex[:8]
venue = Venue.objects.create(name="Browser verification", slug="browser-" + suffix)
staff = StaffMember.objects.create(display_name="Browser", login_identifier="browser-" + suffix)
staff.set_pin("1234"); staff.save()
VenueStaffMembership.objects.create(venue=venue, staff_member=staff, role=StaffRole.MANAGER)
Product.objects.create(venue=venue, name="Browser Beer", price_cents=1200, fulfillment_station="BAR")
table = Table.objects.create(venue=venue, label="Browser", guest_ordering_mode=GuestOrderingMode.DIRECT)
base = "http://127.0.0.1:18765"
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(**({"executable_path": os.environ["CHROMIUM_EXECUTABLE"]} if os.environ.get("CHROMIUM_EXECUTABLE") else {}), args=["--no-sandbox"])
    guest = browser.new_context(viewport={"width": 390, "height": 844})
    page = guest.new_page()
    page.goto(base + "/guest/" + table.public_token)
    page.get_by_role("button", name="Abrir minha comanda").click()
    page.get_by_role("button", name="Browser Beer").click()
    page.get_by_role("button", name="Enviar").click()
    page.get_by_text("Confirmado", exact=True).wait_for()
    page.reload()
    page.get_by_text("Confirmado", exact=True).wait_for()
    manager = browser.new_context(viewport={"width": 390, "height": 844})
    login = manager.request.post(base + "/api/auth/login", data={"venue_slug": venue.slug, "login_identifier": staff.login_identifier, "pin": "1234"})
    assert login.ok, login.text()
    production = manager.new_page(); production.goto(base + "/bar")
    production.get_by_text("1× Browser Beer").wait_for()
    dispatch_pending()
    production.get_by_role("button", name=re.compile("^Aceitar:")).click(); dispatch_pending()
    page.get_by_text("Aceito", exact=True).wait_for()
    production.get_by_role("button", name=re.compile("^Preparar:")).click(); dispatch_pending()
    page.get_by_text("Em preparo", exact=True).wait_for()
    started = time.monotonic()
    production.get_by_role("button", name=re.compile("^Pronto:")).click(); dispatch_pending()
    page.get_by_text("Pronto", exact=True).wait_for()
    readiness_ms = round((time.monotonic() - started) * 1000)
    for name, surface in [("guest", page), ("bar", production)]:
        assert surface.evaluate("document.documentElement.scrollWidth <= innerWidth"), name + " overflows"
        surface.screenshot(path=f"/tmp/rodada-realtime-{name}-390.png", full_page=True)
    page.reload(); page.get_by_text("Pronto", exact=True).wait_for()
    management = manager.new_page(); management.goto(base + "/manage")
    management.get_by_role("heading", name="O que precisa de atenção").wait_for()
    assert management.evaluate("document.documentElement.scrollWidth <= innerWidth")
    management.screenshot(path="/tmp/rodada-realtime-management-390.png", full_page=True)
    # Entirely disconnected reload must start from the cached shell, and never
    # present private history or a command as confirmed from local data.
    page.wait_for_function("async () => !!(await caches.open('rodada-operational-shell-v1')).match(location.href)")
    guest.set_offline(True)
    page.reload(wait_until="domcontentloaded")
    page.get_by_role("heading", name="Cardápio salvo").wait_for()
    page.get_by_text("API indisponível · dados em cache", exact=False).wait_for()
    assert page.get_by_role("button", name=re.compile("^Enviar")).count() == 0
    assert page.get_by_text("Pronto", exact=True).count() == 0
    page.screenshot(path="/tmp/rodada-realtime-guest-offline-390.png", full_page=True)
    production.wait_for_function("async () => !!(await caches.open('rodada-operational-shell-v1')).match(location.href)")
    manager.set_offline(True)
    production.reload(wait_until="domcontentloaded")
    production.get_by_text("1× Browser Beer", exact=True).wait_for()
    production.get_by_text("API indisponível · dados em cache", exact=False).wait_for()
    assert production.get_by_role("button", name="Indisponibilizar Browser Beer", exact=True).is_disabled()
    production.screenshot(path="/tmp/rodada-realtime-bar-offline-390.png", full_page=True)
    print(json.dumps({"guest_reload_history": "passed", "offline_shell_and_safe_cache": "passed", "live_readiness_ms": readiness_ms, "mobile_overflow": "none", "surfaces": ["guest", "bar", "management"]}))
    browser.close()
