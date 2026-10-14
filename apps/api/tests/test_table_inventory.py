from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.db import close_old_connections, connection
from django.test import TransactionTestCase

from modules.access.context import ActorContext
from modules.audit.models import AuditEvent
from modules.hospitality.models import Table, TableOccupancy, TableStatus
from modules.hospitality.services import HospitalityServiceError, occupy_table
from modules.hospitality.table_inventory import set_table_enabled, set_working_table_count
from modules.venue.models import Venue
from tests.test_hospitality_tables import HospitalityTableApiTests


class InventoryApiTests(HospitalityTableApiTests):
    def test_quantity_reuses_tables_and_replay_preserves_audit(self):
        client = self.manager_client()
        old = self.table("Varanda")
        old.status = TableStatus.OUT_OF_SERVICE
        old.save()
        payload = {"target_count": 3, "expected_count": 0}
        response = client.post("/hospitality/tables/count/", payload, format="json")
        assert response.status_code == 200
        old.refresh_from_db()
        assert old.status == TableStatus.AVAILABLE
        assert Table.objects.filter(venue=self.venue).count() == 3
        events = AuditEvent.objects.count()
        assert client.post("/hospitality/tables/count/", payload, format="json").status_code == 200
        assert AuditEvent.objects.count() == events
        assert AuditEvent.objects.filter(
            event_type="table.inventory_changed", actor_staff__isnull=False
        ).exists()

    def test_duplicate_label_returns_conflict(self):
        client = self.manager_client()
        self.table("Mesa A")
        response = client.post("/hospitality/tables/", {"label": "Mesa A"}, format="json")
        assert response.status_code == 409
        assert response.json()["code"] == "TABLE_LABEL_EXISTS"
        assert Table.objects.filter(venue=self.venue, label="Mesa A").count() == 1

    def test_retirement_preserves_token_and_reactivation(self):
        client = self.manager_client()
        table = self.table()
        token = table.public_token
        payload = {"enabled": False, "expected_status": "AVAILABLE"}
        path = f"/hospitality/tables/{table.id}/inventory/"
        assert client.post(path, payload, format="json").status_code == 200
        assert client.post(path, payload, format="json").status_code == 200
        table.refresh_from_db()
        assert table.status == TableStatus.OUT_OF_SERVICE
        assert table.public_token == token
        assert table.access_generation == 2
        assert (
            client.post(
                path, {"enabled": True, "expected_status": "OUT_OF_SERVICE"}, format="json"
            ).status_code
            == 200
        )
        table.refresh_from_db()
        assert table.status == TableStatus.AVAILABLE

    def test_busy_and_cleaning_tables_cannot_be_removed(self):
        client = self.manager_client()
        for status in (TableStatus.OCCUPIED, TableStatus.DIRTY, TableStatus.CLEANING):
            table = self.table(status)
            table.status = status
            table.save()
            response = client.post(
                f"/hospitality/tables/{table.id}/inventory/",
                {"enabled": False, "expected_status": status},
                format="json",
            )
            assert response.status_code == 409
            table.refresh_from_db()
            assert table.status == status

    def test_reduce_is_atomic_and_requires_explicit_selection(self):
        client = self.manager_client()
        first, busy = self.table("A"), self.table("B")
        busy.status = TableStatus.OCCUPIED
        busy.save()
        response = client.post(
            "/hospitality/tables/count/",
            {"target_count": 0, "expected_count": 2, "retire_ids": [str(first.id), str(busy.id)]},
            format="json",
        )
        assert response.status_code == 409
        first.refresh_from_db()
        assert first.status == TableStatus.AVAILABLE
        assert (
            client.post(
                "/hospitality/tables/count/",
                {"target_count": 1, "expected_count": 2},
                format="json",
            ).status_code
            == 409
        )
        assert (
            client.post(
                "/hospitality/tables/count/",
                {"target_count": 1, "expected_count": 2, "retire_ids": [str(first.id)]},
                format="json",
            ).status_code
            == 200
        )

    def test_permission_tenant_conflict_and_validation(self):
        table = self.table()
        body = {"enabled": False, "expected_status": "AVAILABLE"}
        assert (
            self.client.post(
                f"/hospitality/tables/{table.id}/inventory/", body, format="json"
            ).status_code
            == 403
        )
        assert (
            self.client.post(
                "/hospitality/tables/count/",
                {"target_count": 2, "expected_count": 1},
                format="json",
            ).status_code
            == 403
        )
        client = self.manager_client()
        foreign = Table.objects.create(venue=self.other_venue, label="Outra")
        assert (
            client.post(
                f"/hospitality/tables/{foreign.id}/inventory/", body, format="json"
            ).status_code
            == 404
        )
        assert (
            client.post(
                "/hospitality/tables/count/",
                {"target_count": 0, "expected_count": 1, "retire_ids": [str(foreign.id)]},
                format="json",
            ).status_code
            == 409
        )
        assert (
            client.post(
                "/hospitality/tables/count/",
                {"target_count": 2, "expected_count": 0},
                format="json",
            ).status_code
            == 409
        )
        assert (
            client.post(
                "/hospitality/tables/count/",
                {"target_count": -1, "expected_count": 1},
                format="json",
            ).status_code
            == 400
        )
        assert (
            client.post(
                "/hospitality/tables/count/",
                {"target_count": 501, "expected_count": 1},
                format="json",
            ).status_code
            == 400
        )
        foreign.refresh_from_db()
        assert foreign.status == TableStatus.AVAILABLE

    def test_active_occupancy_blocks_even_inconsistent_available_state(self):
        client = self.manager_client()
        table = self.table()
        TableOccupancy.objects.create(table=table, generation=1)
        assert (
            client.post(
                f"/hospitality/tables/{table.id}/inventory/",
                {"enabled": False, "expected_status": "AVAILABLE"},
                format="json",
            ).status_code
            == 409
        )


class InventoryConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Teste", slug="inventory-concurrency")
        self.actor = ActorContext(self.venue.id, None, None, None)

    def race(self, functions):
        assert connection.vendor == "postgresql", "Concurrency proof requires PostgreSQL"
        barrier = Barrier(2)

        def run(function):
            close_old_connections()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET lock_timeout = '5s'")
                barrier.wait(timeout=10)
                try:
                    function()
                    return "OK"
                except HospitalityServiceError as error:
                    return error.code
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            return list(executor.map(run, functions))

    def test_duplicate_quantity_is_serialized(self):
        def configure():
            set_working_table_count(
                target_count=4, expected_count=0, retire_ids=[], actor=self.actor
            )

        assert self.race([configure, configure]) == ["OK", "OK"]
        assert Table.objects.filter(venue=self.venue).count() == 4
        assert AuditEvent.objects.filter(event_type="table.created").count() == 4

    def test_occupy_and_retire_have_one_winner(self):
        table = Table.objects.create(venue=self.venue, label="Mesa")
        results = self.race(
            [
                lambda: occupy_table(table_id=table.id, actor=self.actor),
                lambda: set_table_enabled(
                    table_id=table.id, enabled=False, expected_status="AVAILABLE", actor=self.actor
                ),
            ]
        )
        assert results.count("OK") == 1
        table.refresh_from_db()
        assert table.status in (TableStatus.OCCUPIED, TableStatus.OUT_OF_SERVICE)
        assert table.occupancies.filter(released_at__isnull=True).exists() == (
            table.status == TableStatus.OCCUPIED
        )
