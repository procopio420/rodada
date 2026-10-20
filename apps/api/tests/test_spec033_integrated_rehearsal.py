"""E06 composition rehearsal through real API commands, not UI/hardware acceptance."""

import uuid

import pytest
from django.db import connection
from django.db.models import Sum
from django.test import TestCase
from rest_framework.test import APIClient

from modules.catalog.models import Product
from modules.guest_access.services import GuestAccessError, guest_session_context, resolve_table_qr
from modules.hospitality.models import Table, TableOccupancy
from modules.ledger.models import Charge, Payment
from modules.ordering.models import Order
from tests import test_hospitality_tables as foundation


class IntegratedAttendanceRehearsal(TestCase):
    setUp = foundation.HospitalityTableApiTests.setUp
    manager_client = foundation.HospitalityTableApiTests.manager_client

    def command(self, path, body, *, status=200, client=None):
        response = (client or self.client).post(path, body, format="json")
        assert response.status_code == status, response.json()
        return response.json()

    def test_three_tabs_replay_settlement_and_explicit_turnover(self):
        # Never mistake SQLite's lack of locks for the PostgreSQL integration gate.
        if connection.vendor != "postgresql":
            pytest.skip("E06 integrated rehearsal requires real PostgreSQL")
        self.venue.table_service_enabled = True
        self.venue.save(update_fields=["table_service_enabled"])
        manager = self.manager_client()
        table = Table.objects.create(
            venue=self.venue, label="Same label", guest_ordering_mode="JOIN_ACTIVE"
        )
        foreign_table = Table.objects.create(venue=self.other_venue, label=table.label)
        occupancy = self.command(f"/hospitality/tables/{table.id}/occupy/", {}, status=201)
        guest = resolve_table_qr(public_token=table.public_token)
        products = [
            Product.objects.create(
                venue=self.venue, name=station, price_cents=1200,
                fulfillment_station=station,
            )
            for station in ("BAR", "KITCHEN")
        ]
        tab_ids = []
        for index in range(3):
            opened = self.command(
                f"/hospitality/occupancies/{occupancy['id']}/tabs/open/",
                {"idempotency_key": f"tab-{index}", "expected_generation": occupancy["generation"],
                 "display_label": "Same person label"}, status=201,
            )
            tab_id = opened["tab_id"]
            tab_ids.append(tab_id)
            order_body = {
                "idempotency_key": str(uuid.uuid4()),
                "lines": [{"product_id": str(p.id), "quantity": 1} for p in products],
            }
            confirmed = self.command(f"/tabs/{tab_id}/orders/confirm/", order_body, status=201)
            # Commit followed by an identical retry: server replay, not a network simulation.
            replay = self.command(f"/tabs/{tab_id}/orders/confirm/", order_body)
            assert replay["id"] == confirmed["id"]
            detail = self.client.get(f"/tabs/{tab_id}/").json()
            assert detail["exposure_cents"] == 2400
            assert {i["fulfillment_station_snapshot"] for i in detail["orders"][0]["items"]} == {
                "BAR", "KITCHEN"
            }
            for item in detail["orders"][0]["items"]:
                for state in ("ACCEPTED", "PREPARING", "READY"):
                    self.command(f"/order-items/{item['id']}/transition/", {"state": state},
                                 client=manager)
            tasks = self.client.get("/dispatch/delivery/").json()["results"]
            item_ids = {i["id"] for i in detail["orders"][0]["items"]}
            own = [task for task in tasks if task["order_item_id"] in item_ids]
            assert len(own) == 2
            for task in own:
                self.command(f"/dispatch/delivery/{task['id']}/complete/", {})
            partial = {"amount_cents": 1000, "method": "EXTERNAL_TERMINAL",
                       "idempotency_key": f"partial-{tab_id}"}
            receipt = self.command(f"/tabs/{tab_id}/payments/", partial, status=201,
                                   client=manager)
            assert self.command(f"/tabs/{tab_id}/payments/", partial, status=201, client=manager)["id"] == receipt["id"]
            assert self.client.get(f"/tabs/{tab_id}/").json()["state"] == "OPEN"
            final = {**partial, "amount_cents": 1400, "idempotency_key": f"final-{tab_id}"}
            paid = self.command(f"/tabs/{tab_id}/payments/", final, status=201, client=manager)
            assert self.command(f"/tabs/{tab_id}/payments/", final, status=201, client=manager)["id"] == paid["id"]
            settled = self.client.get(f"/tabs/{tab_id}/").json()
            assert settled["state"] == "CLOSED" and settled["exposure_cents"] == 0
            table.refresh_from_db()
            assert table.status == "OCCUPIED"  # Includes the last Tab: never auto-release.
        assert len(set(tab_ids)) == 3
        assert Order.objects.filter(tab_id__in=tab_ids).count() == 3
        assert Charge.objects.filter(tab_id__in=tab_ids).count() == 6
        assert all(Charge.objects.filter(tab_id=tab_id).count() == 2 for tab_id in tab_ids)
        assert all(Charge.objects.filter(tab_id=tab_id).aggregate(total=Sum("amount_cents"))["total"] == 2400 for tab_id in tab_ids)
        assert Payment.objects.filter(tab_id__in=tab_ids).count() == 6
        assert self.client.get("/dispatch/delivery/").json()["results"] == []
        foreign = self.client.post(
            f"/hospitality/tables/{foreign_table.id}/release/",
            {"expected_occupancy_id": occupancy["id"],
             "expected_generation": occupancy["generation"]}, format="json",
        )
        assert foreign.status_code == 404
        foreign_table.refresh_from_db()
        assert foreign_table.status == "AVAILABLE"
        self.command(f"/hospitality/tables/{table.id}/release/", {
            "expected_occupancy_id": occupancy["id"],
            "expected_generation": occupancy["generation"],
        })
        table.refresh_from_db()
        assert table.status == "DIRTY"
        with self.assertRaises(GuestAccessError):
            guest_session_context(session_token=guest.token)
        for action, expected in (("start", "CLEANING"), ("complete", "AVAILABLE")):
            self.command(f"/hospitality/tables/{table.id}/cleaning/{action}/", {})
            table.refresh_from_db()
            assert table.status == expected
        next_visit = self.command(f"/hospitality/tables/{table.id}/occupy/", {}, status=201)
        assert next_visit["id"] != occupancy["id"]
        assert next_visit["generation"] > occupancy["generation"]
        assert TableOccupancy.objects.filter(table=table, released_at__isnull=True).count() == 1
        assert APIClient().get(f"/tabs/{tab_ids[0]}/").status_code in (401, 403)
