"""Exercise the demo's real staff API path against the configured database.

This is deliberately an API-level smoke test rather than a fixture-only check. It
uses the same login, authorization and mutation routes used by the staff clients.
"""

from uuid import uuid4

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from rest_framework.test import APIClient

from pos.models import Venue


class Command(BaseCommand):
    help = "Run the seeded staff -> order -> production -> payment -> close demo loop."

    def _request(self, client, method, path, payload=None, expected=200):
        response = getattr(client, method)(path, payload or {}, format="json")
        if response.status_code != expected:
            try:
                detail = response.json()
            except ValueError:
                detail = response.content.decode(errors="replace")
            raise CommandError(f"{method.upper()} {path} returned {response.status_code}, expected {expected}: {detail}")
        return response.json()

    def _login(self, venue_id, display_name, pin):
        client = APIClient()
        payload = self._request(
            client,
            "post",
            "/api/auth/login/",
            {"venue_id": venue_id, "display_name": display_name, "pin": pin},
            expected=201,
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {payload['session_token']}")
        return client, payload["staff"]

    def handle(self, *args, **options):
        call_command("seed_demo")
        venue = Venue.objects.get(name="Bar do Aderlan")
        waiter, waiter_staff = self._login(venue.id, "Bia Staff", "1234")
        manager, manager_staff = self._login(venue.id, "Ana Gerente", "0420")
        if waiter_staff["venue_id"] != venue.id or manager_staff["venue_id"] != venue.id:
            raise CommandError("Demo staff login returned the wrong venue.")

        products = self._request(waiter, "get", "/api/products/")
        by_name = {product["name"]: product for product in products}
        try:
            brahma, fritas = by_name["Brahma 600ml"], by_name["Fritas"]
        except KeyError as exc:
            raise CommandError(f"Seeded demo product is missing: {exc.args[0]}") from exc

        run_id = uuid4().hex[:12]

        # A draft cart must still be rejected when availability changes before confirm.
        stale_tab = self._request(
            waiter, "post", "/api/tabs/",
            {"venue_id": venue.id, "label": f"Smoke stale cart {run_id}"}, expected=201,
        )
        stale_order = self._request(
            waiter, "post", f"/api/tabs/{stale_tab['id']}/orders/",
            {"items": [{"product_id": fritas["id"], "quantity": 1}], "idempotency_key": f"stale-{run_id}"},
            expected=201,
        )
        self._request(manager, "post", f"/api/products/{fritas['id']}/availability/", {"available": False})
        try:
            rejected = waiter.post(f"/api/orders/{stale_order['id']}/confirm/", {}, format="json")
            if rejected.status_code != 400:
                raise CommandError(f"Unavailable stale cart was accepted: {rejected.status_code} {rejected.content!r}")
        finally:
            self._request(manager, "post", f"/api/products/{fritas['id']}/availability/", {"available": True})
        self._request(manager, "post", f"/api/tabs/{stale_tab['id']}/close/", {})

        tab = self._request(
            waiter, "post", "/api/tabs/",
            {"venue_id": venue.id, "label": f"Smoke end-to-end {run_id}"}, expected=201,
        )
        order = self._request(
            waiter, "post", f"/api/tabs/{tab['id']}/orders/",
            {
                "items": [
                    {"product_id": brahma["id"], "quantity": 4},
                    {"product_id": fritas["id"], "quantity": 1},
                ],
                "idempotency_key": f"order-{run_id}",
            },
            expected=201,
        )
        confirmed = self._request(waiter, "post", f"/api/orders/{order['id']}/confirm/", {})
        # A confirmation replay must preserve the exact once-only financial effect.
        replayed = self._request(waiter, "post", f"/api/orders/{order['id']}/confirm/", {})
        if replayed["id"] != confirmed["id"]:
            raise CommandError("Order confirmation replay did not return the same order.")

        detail = self._request(waiter, "get", f"/api/tabs/{tab['id']}/")
        expected_total = 4 * brahma["current_price_cents"] + fritas["current_price_cents"]
        if detail["exposure_cents"] != expected_total:
            raise CommandError(f"Expected exposure {expected_total}, received {detail['exposure_cents']}.")
        if {item["unit_price_cents"] for item in confirmed["items"]} != {
            brahma["current_price_cents"], fritas["current_price_cents"]
        }:
            raise CommandError("Confirmed order did not retain unit-price snapshots.")

        # Bar can go straight to READY after acceptance; kitchen also demonstrates PREPARING.
        for item in confirmed["items"]:
            self._request(waiter, "post", f"/api/order-items/{item['id']}/transition/", {"state": "ACCEPTED"})
            if item["fulfillment_station"] == "KITCHEN":
                self._request(waiter, "post", f"/api/order-items/{item['id']}/transition/", {"state": "PREPARING"})
            self._request(waiter, "post", f"/api/order-items/{item['id']}/transition/", {"state": "READY"})

        tasks = self._request(waiter, "get", f"/api/dispatch/tasks/?venue_id={venue.id}")
        delivery_tasks = [task for task in tasks if task["order_item_id"] in {item["id"] for item in confirmed["items"]}]
        if len(delivery_tasks) != len(confirmed["items"]):
            raise CommandError("READY order items did not create their persisted delivery work.")
        for task in delivery_tasks:
            self._request(waiter, "post", f"/api/dispatch/tasks/{task['id']}/claim/", {})
            self._request(waiter, "post", f"/api/dispatch/tasks/{task['id']}/done/", {})

        cannot_close = manager.post(f"/api/tabs/{tab['id']}/close/", {}, format="json")
        if cannot_close.status_code != 400:
            raise CommandError("Tab closed before its outstanding balance was paid.")

        partial_cents = expected_total // 2
        partial = self._request(
            manager, "post", f"/api/tabs/{tab['id']}/payments/",
            {"amount_cents": partial_cents, "method": "CASH", "idempotency_key": f"partial-{run_id}"}, expected=201,
        )
        if partial["exposure_cents"] != expected_total - partial_cents:
            raise CommandError("Partial payment did not reduce open exposure.")
        paid = self._request(
            manager, "post", f"/api/tabs/{tab['id']}/payments/",
            {"amount_cents": expected_total - partial_cents, "method": "CARD", "idempotency_key": f"final-{run_id}"}, expected=201,
        )
        if paid["exposure_cents"] != 0:
            raise CommandError("Final payment did not settle the tab.")
        closed = self._request(manager, "post", f"/api/tabs/{tab['id']}/close/", {})
        if closed["status"] != "CLOSED":
            raise CommandError("Settled tab did not close.")
        closed_order = waiter.post(
            f"/api/tabs/{tab['id']}/orders/",
            {"items": [{"product_id": brahma["id"], "quantity": 1}]}, format="json",
        )
        if closed_order.status_code != 400:
            raise CommandError("Closed tab accepted a new order.")

        self.stdout.write(self.style.SUCCESS(
            f"Demo smoke passed: tab #{tab['id']}, order #{order['id']}, exposure {expected_total} -> 0."
        ))
