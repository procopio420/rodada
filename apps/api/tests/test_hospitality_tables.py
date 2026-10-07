from django.test import TestCase
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.hospitality.models import Table, TableStatus
from modules.ordering.models import Tab, TabState
from modules.venue.models import Venue


class HospitalityTableApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.venue = Venue.objects.create(name="Bar", slug="hospitality-bar")
        self.other_venue = Venue.objects.create(name="Outro", slug="hospitality-other")
        self.staff = StaffMember.objects.create(
            display_name="Ana", login_identifier="hospitality-ana"
        )
        self.staff.set_pin("1234")
        self.staff.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(
            venue=self.venue, staff_member=self.staff, role=StaffRole.STAFF
        )
        login = self.client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": self.staff.login_identifier,
                "pin": "1234",
                "installation_id": "hospitality-device",
                "platform": "WEB",
            },
            format="json",
        )
        assert login.status_code == 200, login.json()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])

    def table(self, label="12"):
        return Table.objects.create(venue=self.venue, label=label)

    def tab(self, label=""):
        return Tab.objects.create(venue=self.venue, display_label=label)

    def test_table_has_opaque_stable_public_token(self):
        table = self.table()
        second = self.table("13")

        assert table.public_token != str(table.id)
        assert len(table.public_token) >= 32
        assert table.public_token != second.public_token
        original = table.public_token
        table.label = "Varanda 12"
        table.save(update_fields=["label"])
        table.refresh_from_db()
        assert table.public_token == original

    def test_lifecycle_accepts_multiple_tabs_and_audits_actors(self):
        table = self.table()
        first_tab = self.tab("João")
        second_tab = self.tab("Ana")

        occupied = self.client.post(
            f"/hospitality/tables/{table.id}/occupy/", {"tab_id": str(first_tab.id)}, format="json"
        )
        assert occupied.status_code == 201, occupied.json()
        occupancy_id = occupied.json()["id"]
        assert occupied.json()["generation"] == 1
        assert occupied.json()["tabs"] == [{"id": str(first_tab.id), "display_label": "João"}]

        assigned = self.client.post(
            f"/hospitality/occupancies/{occupancy_id}/tabs/",
            {"tab_id": str(second_tab.id)},
            format="json",
        )
        assert assigned.status_code == 201, assigned.json()
        table.refresh_from_db()
        assert table.status == TableStatus.OCCUPIED
        assert table.access_generation == 1

        # Tab settlement never releases a physical resource by itself.
        first_tab.state = TabState.CLOSED
        first_tab.save(update_fields=["state"])
        table.refresh_from_db()
        assert table.status == TableStatus.OCCUPIED

        released = self.client.post(f"/hospitality/tables/{table.id}/release/", format="json")
        assert released.status_code == 200, released.json()
        assert released.json()["released_at"] is not None
        table.refresh_from_db()
        assert table.status == TableStatus.DIRTY
        assert table.access_generation == 1

        cleaning = self.client.post(
            f"/hospitality/tables/{table.id}/cleaning/start/", format="json"
        )
        assert cleaning.status_code == 200, cleaning.json()
        table.refresh_from_db()
        assert table.status == TableStatus.CLEANING
        assert table.access_generation == 1

        complete = self.client.post(
            f"/hospitality/tables/{table.id}/cleaning/complete/", format="json"
        )
        assert complete.status_code == 200, complete.json()
        table.refresh_from_db()
        assert table.status == TableStatus.AVAILABLE
        assert table.access_generation == 2

        events = AuditEvent.objects.filter(venue=self.venue, entity_id=occupancy_id)
        assert set(events.values_list("event_type", flat=True)) == {
            "table.occupied",
            "table.released",
            "table.cleaning_started",
            "table.cleaning_completed",
        }
        assert (
            not events.filter(actor_staff_id=self.staff.id)
            .exclude(actor_session_id__isnull=False)
            .exists()
        )

    def test_rejects_invalid_lifecycle_transition_without_generation_change(self):
        table = self.table()

        response = self.client.post(
            f"/hospitality/tables/{table.id}/cleaning/complete/", format="json"
        )
        assert response.status_code == 409
        assert response.json()["code"] == "INVALID_TABLE_TRANSITION"
        table.refresh_from_db()
        assert table.status == TableStatus.AVAILABLE
        assert table.access_generation == 1

    def test_tab_cannot_be_assigned_to_two_active_occupancies(self):
        tab = self.tab("Grupo")
        first = self.table("1")
        second = self.table("2")
        first_occupied = self.client.post(
            f"/hospitality/tables/{first.id}/occupy/", {"tab_id": str(tab.id)}, format="json"
        )
        assert first_occupied.status_code == 201, first_occupied.json()
        second_occupied = self.client.post(
            f"/hospitality/tables/{second.id}/occupy/", format="json"
        )
        assert second_occupied.status_code == 201, second_occupied.json()

        response = self.client.post(
            f"/hospitality/occupancies/{second_occupied.json()['id']}/tabs/",
            {"tab_id": str(tab.id)},
            format="json",
        )
        assert response.status_code == 409
        assert response.json()["code"] == "TAB_ALREADY_OCCUPIED"
        assert response.json()["occupancy_id"] == first_occupied.json()["id"]

    def test_venue_isolation_hides_tables_and_tabs(self):
        other_table = Table.objects.create(venue=self.other_venue, label="Other")
        other_tab = Tab.objects.create(venue=self.other_venue)
        local = self.table()

        assert (
            self.client.post(
                f"/hospitality/tables/{other_table.id}/occupy/", format="json"
            ).status_code
            == 404
        )
        response = self.client.post(
            f"/hospitality/tables/{local.id}/occupy/", {"tab_id": str(other_tab.id)}, format="json"
        )
        assert response.status_code == 404
        assert response.json()["code"] == "TAB_NOT_FOUND"

    def test_table_creation_requires_venue_configuration(self):
        response = self.client.post("/hospitality/tables/", {"label": "Criação"}, format="json")
        assert response.status_code == 403
