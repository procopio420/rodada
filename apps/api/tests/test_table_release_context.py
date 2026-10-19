"""Spec033 release uses canonical occupancy context under lifecycle locks."""

from django.test import TestCase

from modules.audit.models import AuditEvent
from modules.guest_access.services import GuestAccessError, guest_session_context, resolve_table_qr
from modules.hospitality.models import Table, TableOccupancy, TabOccupancyAssignment
from tests import test_hospitality_tables as fixtures


class TableReleaseContextTests(TestCase):
    setUp = fixtures.HospitalityTableApiTests.setUp
    table = fixtures.HospitalityTableApiTests.table
    tab = fixtures.HospitalityTableApiTests.tab

    def occupied(self):
        table = self.table()
        table.guest_ordering_mode = "JOIN_ACTIVE"
        table.save(update_fields=["guest_ordering_mode"])
        result = self.client.post(
            f"/hospitality/tables/{table.id}/occupy/",
            {"tab_id": str(self.tab("Marina").id)},
            format="json",
        )
        assert result.status_code == 201
        return table, TableOccupancy.objects.get(pk=result.json()["id"])

    def release(self, table, payload):
        return self.client.post(f"/hospitality/tables/{table.id}/release/", payload, format="json")

    def snapshot(self, table):
        return (
            list(Table.objects.filter(pk=table.id).values()),
            list(TableOccupancy.objects.filter(table=table).values()),
            list(TabOccupancyAssignment.objects.filter(occupancy__table=table).values()),
            list(AuditEvent.objects.values()),
        )

    def test_matching_context_releases_and_revokes_guest_access(self):
        table, occupancy = self.occupied()
        guest = resolve_table_qr(public_token=table.public_token)
        assert guest_session_context(session_token=guest.token).occupancy_id == occupancy.id
        result = self.release(
            table,
            {
                "expected_occupancy_id": str(occupancy.id),
                "expected_generation": occupancy.generation,
            },
        )
        assert result.status_code == 200, result.json()
        table.refresh_from_db()
        assert table.status == "DIRTY"
        assert not TabOccupancyAssignment.objects.filter(
            occupancy=occupancy, released_at__isnull=True
        ).exists()
        assert (
            AuditEvent.objects.filter(
                event_type="table.released", entity_id=str(occupancy.id)
            ).count()
            == 1
        )
        with self.assertRaises(GuestAccessError) as error:
            guest_session_context(session_token=guest.token)
        assert error.exception.code == "GUEST_SESSION_REVOKED"

    def test_replacement_occupancy_rejects_original_id_without_writes(self):
        table, original = self.occupied()
        assert (
            self.release(
                table,
                {
                    "expected_occupancy_id": str(original.id),
                    "expected_generation": original.generation,
                },
            ).status_code
            == 200
        )
        for command in ["cleaning/start", "cleaning/complete", "occupy"]:
            result = self.client.post(
                f"/hospitality/tables/{table.id}/{command}/", {}, format="json"
            )
            assert result.status_code in [200, 201], result.json()
        current = TableOccupancy.objects.get(table=table, released_at__isnull=True)
        guest = resolve_table_qr(public_token=table.public_token)
        before = self.snapshot(table)
        for payload in [
            {"expected_occupancy_id": str(original.id), "expected_generation": original.generation},
            {"expected_occupancy_id": str(current.id), "expected_generation": original.generation},
        ]:
            result = self.release(table, payload)
            assert result.status_code == 409 and result.json()["code"] == "STALE_OCCUPANCY", (
                result.json()
            )
            assert self.snapshot(table) == before
            assert guest_session_context(session_token=guest.token).occupancy_id == current.id

    def test_invalid_pairs_are_rejected_without_writes(self):
        table, occupancy = self.occupied()
        before = self.snapshot(table)
        for payload in [
            {},
            {"expected_occupancy_id": str(occupancy.id)},
            {"expected_generation": occupancy.generation},
            {"expected_occupancy_id": "invalid", "expected_generation": 1},
            {"expected_occupancy_id": str(occupancy.id), "expected_generation": 0},
            {"expected_occupancy_id": None, "expected_generation": None},
        ]:
            assert self.release(table, payload).status_code == 400
            assert self.snapshot(table) == before

    def test_foreign_table_is_not_found(self):
        table = Table.objects.create(venue=self.other_venue, label="Other", status="OCCUPIED")
        occupancy = TableOccupancy.objects.create(table=table, generation=1)
        before = self.snapshot(table)
        result = self.release(
            table, {"expected_occupancy_id": str(occupancy.id), "expected_generation": 1}
        )
        assert result.status_code == 404 and result.json()["code"] == "TABLE_NOT_FOUND"
        assert self.snapshot(table) == before

    def test_omitted_context_is_required(self):
        table, occupancy = self.occupied()
        assert self.release(table, {}).status_code == 400
        occupancy.refresh_from_db()
        assert occupancy.released_at is None
