"""Authorized concurrent membership edits use real PostgreSQL row locks."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import connection, connections
from django.test import TransactionTestCase
from rest_framework.test import APIClient

from modules.access.models import StaffMember, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.venue.models import Venue


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks")
class AccessConcurrencyTests(TransactionTestCase):
    def test_two_managers_edit_one_membership_and_loser_receives_current_state(self):
        venue = Venue.objects.create(name="Access race", slug="access-race")
        target = StaffMember.objects.create(display_name="Waiter", login_identifier="access-target")
        membership = VenueStaffMembership.objects.create(venue=venue, staff_member=target)
        tokens = []
        for index in range(2):
            staff = StaffMember.objects.create(
                display_name=f"Manager {index}", login_identifier=f"race-{index}"
            )
            staff.set_pin("2468")
            staff.save(update_fields=["pin_hash"])
            VenueStaffMembership.objects.create(
                venue=venue,
                staff_member=staff,
                role="MANAGER",
                capability_overrides={"allow": ["staff.manage"]},
            )
            client = APIClient()
            login = client.post(
                "/auth/login/",
                {
                    "venue_slug": venue.slug,
                    "login_identifier": staff.login_identifier,
                    "pin": "2468",
                    "installation_id": f"race-device-{index}",
                    "platform": "WEB",
                },
                format="json",
            )
            assert login.status_code == 200, login.data
            token = login.data["access_token"]
            client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
            assert (
                client.post("/auth/reauthenticate/", {"pin": "2468"}, format="json").status_code
                == 200
            )
            tokens.append(token)
        barrier = Barrier(2)

        def edit(values):
            token, role = values
            try:
                client = APIClient()
                client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
                barrier.wait(timeout=10)
                response = client.patch(
                    f"/manage/access/memberships/{membership.pk}/",
                    {"expected_version": 1, "role": role},
                    format="json",
                )
                return response.status_code, response.json()
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(edit, zip(tokens, ["CASHIER", "MANAGER"])))
        assert sorted(status for status, _ in results) == [200, 409], results
        winner = next(body for status, body in results if status == 200)
        loser = next(body for status, body in results if status == 409)
        assert loser["code"] == "VERSION_CONFLICT"
        assert loser["current"]["id"] == str(membership.pk)
        assert loser["current"]["version"] == winner["version"] == 2
        assert loser["current"]["role"] == winner["role"]
        membership.refresh_from_db()
        assert membership.role == winner["role"] and membership.version == 2
        assert (
            AuditEvent.objects.filter(venue=venue, event_type="membership.role_changed").count()
            == 1
        )
