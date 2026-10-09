from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase

from modules.access.context import ActorContext
from modules.access.models import StaffMember, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.guest_access.services import create_or_get_guest_tab, resolve_table_qr
from modules.hospitality.models import (
    PartySizeObservation,
    Table,
    TableOccupancy,
    TabOccupancyAssignment,
)
from modules.hospitality.party_size import (
    current_party_size,
    observation_payload,
    record_party_size,
)
from modules.hospitality.services import HospitalityServiceError, release_table
from modules.ordering.models import Tab
from modules.venue.models import Venue


class Fixture:
    def setUp(self):
        self.venue = Venue.objects.create(name="Covers", slug="covers")
        self.staff = StaffMember.objects.create(display_name="Ana", login_identifier="covers-ana")
        self.membership = VenueStaffMembership.objects.create(
            venue=self.venue, staff_member=self.staff, role="STAFF"
        )
        self.actor = ActorContext(self.venue.id, self.staff.id, None, None)
        self.table = Table.objects.create(
            venue=self.venue, label="1", status="OCCUPIED", guest_ordering_mode="DIRECT"
        )
        self.occupancy = TableOccupancy.objects.create(table=self.table, generation=1)

    def record(self, count=5, version=0, key="first", **kwargs):
        return record_party_size(
            occupancy_id=self.occupancy.id,
            covers_count=count,
            expected_version=version,
            idempotency_key=key,
            actor=self.actor,
            **kwargs,
        )

    def guest(self):
        resolution = resolve_table_qr(public_token=self.table.public_token)
        create_or_get_guest_tab(session_token=resolution.token)
        return resolution


class PartySizeTests(Fixture, TestCase):
    def test_unknown_multiple_tabs_and_no_financial_mutation(self):
        assert (
            observation_payload(current_party_size(occupancy_id=self.occupancy.id))["covers_count"]
            is None
        )
        tabs = [Tab.objects.create(venue=self.venue) for _ in range(3)]
        for tab in tabs:
            TabOccupancyAssignment.objects.create(occupancy=self.occupancy, tab=tab)
        row = self.record(6)
        assert row.source == "STAFF"
        assert sum(PartySizeObservation.objects.values_list("covers_count", flat=True)) == 6
        for tab in tabs:
            assert current_party_size(tab_id=tab.id).id == row.id
            tab.refresh_from_db()
            assert tab.state == "OPEN"

    def test_correction_history_retry_and_stale_provenance(self):
        first = self.record(4)
        second = self.record(5, 1, "correction")
        assert second.supersedes_id == first.id
        assert self.record(5, 1, "correction").id == second.id
        assert PartySizeObservation.objects.count() == 2
        with self.assertRaises(HospitalityServiceError) as error:
            self.record(6, 1, "stale")
        assert error.exception.code == "STALE_PARTY_SIZE"
        assert error.exception.details["current"]["covers_count"] == 5
        with self.assertRaises(HospitalityServiceError) as error:
            self.record(6, 2, "correction")
        assert error.exception.code == "IDEMPOTENCY_CONFLICT"

    def test_post_release_manager_reason_and_snapshot(self):
        first = self.record(5)
        release_table(table_id=self.table.id, actor=self.actor)
        snapshot = AuditEvent.objects.get(event_type="table.released").metadata["party_size"]
        with self.assertRaises(HospitalityServiceError) as error:
            self.record(6, 1, "later")
        assert error.exception.code == "MANAGER_REQUIRED"
        self.membership.role = "MANAGER"
        self.membership.save()
        with self.assertRaises(HospitalityServiceError) as error:
            self.record(6, 1, "later")
        assert error.exception.code == "REASON_REQUIRED"
        corrected = self.record(6, 1, "later", reason="Pessoa adicional")
        assert corrected.supersedes_id == first.id
        assert snapshot == {"observation_id": str(first.id), "covers_count": 5}
        audit = AuditEvent.objects.get(event_type="party_size.corrected")
        assert audit.metadata["previous_count"] == 5
        assert audit.actor_staff_id == self.staff.id
        assert audit.metadata["reason"]

    def test_tab_fallback_not_added_after_occupancy_join(self):
        tab = Tab.objects.create(venue=self.venue)
        standalone = record_party_size(
            tab_id=tab.id,
            covers_count=3,
            expected_version=0,
            idempotency_key="standalone",
            actor=self.actor,
        )
        count = self.record(7)
        TabOccupancyAssignment.objects.create(occupancy=self.occupancy, tab=tab)
        assert current_party_size(tab_id=tab.id).id == count.id
        assert PartySizeObservation.objects.get(pk=standalone.id).covers_count == 3
        with self.assertRaises(HospitalityServiceError) as error:
            record_party_size(
                tab_id=tab.id,
                covers_count=4,
                expected_version=1,
                idempotency_key="bad",
                actor=self.actor,
            )
        assert error.exception.code == "OCCUPANCY_TARGET_REQUIRED"

    def test_guest_provenance_own_target_and_stale_staff_correction(self):
        resolution = self.guest()
        row = record_party_size(
            session_token=resolution.token,
            covers_count=4,
            expected_version=0,
            idempotency_key="guest",
        )
        assert row.source == "GUEST" and row.guest_session_id == resolution.session.id
        self.record(5, 1, "staff-correction")
        with self.assertRaises(HospitalityServiceError) as error:
            record_party_size(
                session_token=resolution.token,
                covers_count=6,
                expected_version=1,
                idempotency_key="stale-guest",
            )
        assert error.exception.code == "STALE_PARTY_SIZE"
        other = TableOccupancy.objects.create(
            table=Table.objects.create(venue=self.venue, label="2"), generation=1
        )
        with self.assertRaises(HospitalityServiceError) as error:
            record_party_size(
                session_token=resolution.token,
                occupancy_id=other.id,
                covers_count=6,
                expected_version=0,
                idempotency_key="other",
            )
        assert error.exception.code == "GUEST_NOT_AUTHORIZED"

    def test_zero_and_cross_venue_rejected(self):
        for count in (0, -1, True, 1.5):
            with self.assertRaises(HospitalityServiceError) as error:
                self.record(count)
            assert error.exception.code == "INVALID_COVER_COUNT"
        venue = Venue.objects.create(name="Other", slug="other-covers")
        actor = ActorContext(venue.id, self.staff.id, None, None)
        VenueStaffMembership.objects.create(venue=venue, staff_member=self.staff, role="STAFF")
        with self.assertRaises(HospitalityServiceError) as error:
            record_party_size(
                actor=actor,
                occupancy_id=self.occupancy.id,
                covers_count=4,
                expected_version=0,
                idempotency_key="idor",
            )
        assert error.exception.code == "OCCUPANCY_NOT_FOUND"


class PartySizeConcurrencyTests(Fixture, TransactionTestCase):
    def test_postgres_guest_staff_race_one_winner(self):
        if connection.vendor != "postgresql":
            self.skipTest("Real row locking requires PostgreSQL")
        resolution = self.guest()
        self.record(3)
        self.record(4, 1, "version-two")
        barrier = Barrier(2)

        def worker(guest):
            close_old_connections()
            barrier.wait()
            try:
                record_party_size(
                    occupancy_id=self.occupancy.id,
                    covers_count=4 if guest else 5,
                    expected_version=2,
                    idempotency_key="race-guest" if guest else "race-staff",
                    actor=None if guest else self.actor,
                    session_token=resolution.token if guest else None,
                )
                return "ok"
            except HospitalityServiceError as error:
                assert error.details["current"]["source"] in ("GUEST", "STAFF")
                return error.code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(worker, (True, False)))
        assert sorted(outcomes) == ["STALE_PARTY_SIZE", "ok"]
        assert PartySizeObservation.objects.count() == 3
        assert current_party_size(occupancy_id=self.occupancy.id).version == 3


class CoverMetricsTests(Fixture, TestCase):
    def test_ratio_of_sums_coverage_and_duplicate_visits(self):
        from modules.hospitality.party_size import occupancy_cover_metrics

        self.record(4)
        other = TableOccupancy.objects.create(
            table=Table.objects.create(venue=self.venue, label="2", status="OCCUPIED"), generation=1
        )
        record_party_size(
            occupancy_id=other.id,
            covers_count=2,
            expected_version=0,
            idempotency_key="second",
            actor=self.actor,
        )
        unknown = TableOccupancy.objects.create(
            table=Table.objects.create(venue=self.venue, label="3"), generation=1
        )
        metrics = occupancy_cover_metrics(
            occupancies=[self.occupancy, other, unknown, self.occupancy],
            eligible_revenue_cents={self.occupancy.id: 10000, other.id: 6000, unknown.id: 5000},
        )
        assert metrics["revenue_per_cover"] == {"numerator_cents": 16000, "denominator_covers": 6}
        assert metrics["known_visits"] == 2 and metrics["unknown_visits"] == 1
        assert metrics["coverage_basis_points"] == 6666
        excluded = occupancy_cover_metrics(
            occupancies=[self.occupancy, other], eligible_revenue_cents={self.occupancy.id: 10000}
        )
        assert excluded["excluded_visits"] == 1
        assert excluded["eligible_known_covers"] == 4


class PartySizeApiTests(Fixture, TestCase):
    def test_real_authenticated_routes_history_and_guest_provenance(self):
        import sys

        from django.test import override_settings
        from rest_framework.test import APIClient

        from rodada_api.urls import urlpatterns as canonical_urls

        module = sys.modules[__name__]
        module.urlpatterns = canonical_urls
        with override_settings(ROOT_URLCONF=__name__):
            self.staff.set_pin("1234")
            self.staff.save()
            client = APIClient()
            login = client.post(
                "/auth/login/",
                {
                    "venue_slug": self.venue.slug,
                    "login_identifier": self.staff.login_identifier,
                    "pin": "1234",
                    "installation_id": "covers-web",
                    "platform": "WEB",
                },
                format="json",
            )
            assert login.status_code == 200, login.json()
            client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
            url = f"/hospitality/occupancies/{self.occupancy.id}/party-size/"
            unknown = client.get(url)
            assert unknown.status_code == 200 and unknown.json()["current"]["covers_count"] is None
            resolution = self.guest()
            guest = APIClient()
            guest.credentials(HTTP_X_GUEST_SESSION=resolution.token)
            response = guest.post(
                "/guest/party-size/",
                {"covers_count": 4, "expected_version": 0, "idempotency_key": "api-guest"},
                format="json",
            )
            assert response.status_code == 200, response.json()
            assert response.json()["source"] == "GUEST"
            assert (
                "staff_member_id" not in response.json()
                and "guest_session_id" not in response.json()
            )
            corrected = client.post(
                url,
                {"covers_count": 5, "expected_version": 1, "idempotency_key": "api-staff", "reason": "Private staff correction"},
                format="json",
            )
            assert corrected.status_code == 200, corrected.json()
            stale = guest.post(
                "/guest/party-size/",
                {"covers_count": 6, "expected_version": 1, "idempotency_key": "guest-stale"},
                format="json",
            )
            assert stale.status_code == 409, stale.json()
            assert set(stale.json()["current"]) == {
                "covers_count", "version", "source", "observation_id"
            }
            assert "Private staff correction" not in str(stale.json())
            history = client.get(url).json()["history"]
            assert [row["covers_count"] for row in history] == [5, 4]
            assert history[0]["source"] == "STAFF"
            release_table(table_id=self.table.id, actor=self.actor)
            response = guest.post(
                "/guest/party-size/",
                {"covers_count": 6, "expected_version": 2, "idempotency_key": "api-after-release"},
                format="json",
            )
            assert response.status_code == 403, response.json()
