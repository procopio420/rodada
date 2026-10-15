"""TableGroup HTTP authorization, isolation, idempotency and identity safety."""
import uuid

from django.test import TestCase
from rest_framework.test import APIClient

from modules.audit.models import AuditEvent
from modules.hospitality.models import Table, TableGroup, TableGroupMembership
from modules.ordering.models import Order, Tab
from tests.test_hospitality_tables import HospitalityTableApiTests


class GroupApiTests(TestCase):
    setUp = HospitalityTableApiTests.setUp

    def set_tables(self):
        return (
            Table.objects.create(venue=self.venue, label="A"),
            Table.objects.create(venue=self.venue, label="B"),
            Table.objects.create(venue=self.venue, label="C"),
        )

    def create_group(self, ids, key=None, label="Juntas"):
        return self.client.post("/hospitality/table-groups/", {
            "table_ids": [str(i) for i in ids],
            "label": label,
            "request_key": str(key or uuid.uuid4()),
        }, format="json")

    def test_create_replay_conflict_and_dissolve_preserve_all_tabs(self):
        a, b, c = self.set_tables()
        token_a, token_b = a.public_token, b.public_token
        tab = Tab.objects.create(venue=self.venue)
        occupied = self.client.post(f"/hospitality/tables/{a.id}/occupy/", {
            "tab_id": str(tab.id),
        }, format="json")
        assert occupied.status_code == 201, occupied.json()
        order = Order.objects.create(tab=tab, source="STAFF")
        key = uuid.uuid4()
        first = self.create_group([b.id, a.id], key=key)
        assert first.status_code == 201, first.json()
        group_id = first.json()["id"]
        assert not first.json()["replayed"]
        assert len(first.json()["tables"]) == 2
        replay = self.create_group([a.id, b.id], key=key)
        assert replay.status_code == 200
        assert replay.json()["replayed"]
        conflict = self.create_group([a.id, c.id], key=key)
        assert conflict.status_code == 409
        assert conflict.json()["code"] == "IDEMPOTENCY_CONFLICT"
        duplicated = self.create_group([a.id, a.id])
        assert duplicated.status_code == 400
        another = self.create_group([a.id, c.id])
        assert another.status_code == 409
        assert another.json()["code"] == "TABLE_ALREADY_GROUPED"

        listing = self.client.get("/hospitality/tables/")
        assert listing.status_code == 200
        by_id = {r["id"]: r for r in listing.json()["results"]}
        assert by_id[str(a.id)]["group"]["id"] == group_id
        assert by_id[str(b.id)]["group"]["id"] == group_id
        assert by_id[str(c.id)]["group"] is None

        dissolved = self.client.post(f"/hospitality/table-groups/{group_id}/dissolve/", format="json")
        assert dissolved.status_code == 200
        assert dissolved.json()["active"] is False
        assert not dissolved.json()["replayed"]
        assert self.client.post(f"/hospitality/table-groups/{group_id}/dissolve/", format="json").json()["replayed"]
        again = self.create_group([a.id, c.id])
        assert again.status_code == 201
        a.refresh_from_db()
        b.refresh_from_db()
        tab.refresh_from_db()
        order.refresh_from_db()
        assert a.public_token == token_a
        assert b.public_token == token_b
        assert tab.venue_id == self.venue.id
        assert order.tab_id == tab.id
        assert a.occupancies.get().pk == uuid.UUID(occupied.json()["id"])
        assert AuditEvent.objects.filter(venue=self.venue, event_type="table_group.created").count() == 2
        assert AuditEvent.objects.filter(venue=self.venue, event_type="table_group.dissolved").count() == 1
        assert TableGroupMembership.objects.filter(table=a, removed_at__isnull=True).count() == 1

    def test_cross_venue_hidden_and_unauthorised(self):
        a, b, _ = self.set_tables()
        outside = Table.objects.create(venue=self.other_venue, label="Secret")
        bad = self.create_group([a.id, outside.id])
        assert bad.status_code == 404
        assert not TableGroup.objects.exists()
        group = self.create_group([a.id, b.id])
        assert group.status_code == 201
        client = APIClient()
        assert client.get("/hospitality/table-groups/").status_code in (401, 403)
        assert client.post(f"/hospitality/table-groups/{group.json()['id']}/dissolve/").status_code in (401, 403)
        assert len(self.client.get("/hospitality/table-groups/").json()["results"]) == 1

    def test_cannot_group_out_of_service_table(self):
        a, b, _ = self.set_tables()
        a.status = "OUT_OF_SERVICE"
        a.save(update_fields=["status"])
        bad = self.create_group([a.id, b.id])
        assert bad.status_code == 409
        assert bad.json()["code"] == "TABLE_OUT_OF_SERVICE"
        assert not TableGroup.objects.exists()

    def test_grouped_table_cannot_be_retired_until_dissolved(self):
        a, b, _ = self.set_tables()
        grouped = self.create_group([a.id, b.id])
        assert grouped.status_code == 201
        manager = HospitalityTableApiTests.manager_client(self)
        retire = manager.post(
            f"/hospitality/tables/{a.id}/inventory/",
            {"enabled": False, "expected_status": "AVAILABLE"}, format="json",
        )
        assert retire.status_code == 409
        assert retire.json()["code"] == "TABLE_GROUP_ACTIVE"
        a.refresh_from_db()
        assert a.status == "AVAILABLE"
        self.client.post(
            f"/hospitality/table-groups/{grouped.json()['id']}/dissolve/", format="json",
        )
        assert manager.post(
            f"/hospitality/tables/{a.id}/inventory/",
            {"enabled": False, "expected_status": "AVAILABLE"}, format="json",
        ).status_code == 200
