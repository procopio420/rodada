from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.test import APIClient

from modules.access.context import ActorContext
from modules.access.models import DeviceRegistration, StaffMember, StaffSession, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.documents_printing.kds import assess_station, configure_detector, heartbeat
from modules.documents_printing.models import KdsDeviceHeartbeat, KdsStationHealth, PrintJob
from modules.venue.models import Venue


class KdsFixture:
    def setUp(self):
        self.now = timezone.now()
        self.venue = Venue.objects.create(name="KDS", slug="kds-health")
        self.staff = StaffMember.objects.create(display_name="Manager", login_identifier="kds-health")
        self.membership = VenueStaffMembership.objects.create(venue=self.venue, staff_member=self.staff, role="MANAGER")
        self.session = self.make_session("first")

    def make_session(self, key):
        device = DeviceRegistration.objects.create(venue=self.venue, installation_key_hash=key, platform="WEB")
        return StaffSession.objects.create(
            venue=self.venue, staff_member=self.staff, membership=self.membership,
            device=device, expires_at=self.now + timedelta(hours=12),
            access_expires_at=self.now + timedelta(hours=12),
        )

    def ping(self, seconds, session=None, observed=True):
        with patch("django.utils.timezone.now", return_value=self.now + timedelta(seconds=seconds)):
            return heartbeat(session_id=(session or self.session).id, station="BAR", queue_observed=observed)

    def assess(self, seconds):
        with patch("django.utils.timezone.now", return_value=self.now + timedelta(seconds=seconds)):
            return assess_station(venue_id=self.venue.id, station="BAR")


class KdsHealthTests(KdsFixture, TestCase):
    def test_sustained_failure_restart_and_recovery_hysteresis(self):
        self.assertEqual(self.ping(0).state, "HEALTHY")
        self.assertEqual(self.assess(31).state, "SUSPECT")
        self.assertEqual(self.assess(119).state, "SUSPECT")
        self.assertEqual(self.assess(120).state, "UNHEALTHY")
        # Separate service calls reload persisted state; no process-local detector timers.
        self.assertEqual(self.ping(121).state, "RECOVERING")
        for second in (140, 160, 180):
            self.assertEqual(self.ping(second).state, "RECOVERING")
        self.assertEqual(self.ping(181).state, "HEALTHY")
        self.assertEqual(PrintJob.objects.count(), 0)

    def test_late_first_evaluation_cannot_hide_failure_with_new_ping(self):
        self.ping(0)
        self.assertEqual(self.ping(121).state, "RECOVERING")
        self.assertEqual(self.ping(152).state, "RECOVERING")
        self.assertEqual(self.assess(182).state, "UNHEALTHY")
        self.assertEqual(self.ping(183).state, "RECOVERING")
        for second in (200, 220, 240):
            self.assertEqual(self.ping(second).state, "RECOVERING")
        self.assertEqual(self.ping(243).state, "HEALTHY")

    def test_station_aggregates_devices_not_one_browser_disconnect(self):
        second = self.make_session("second")
        self.ping(0)
        self.ping(25, second)
        self.assertEqual(self.assess(40).state, "HEALTHY")
        self.assertEqual(KdsDeviceHeartbeat.objects.count(), 2)
        self.assertEqual(self.assess(56).state, "SUSPECT")

    def test_liveness_without_queue_success_is_not_healthy(self):
        self.assertEqual(self.ping(0, observed=False).state, "SUSPECT")
        self.assertEqual(self.ping(90, observed=False).state, "UNHEALTHY")

    def test_failed_read_after_long_healthy_period_starts_new_failure_window(self):
        for second in range(0, 201, 20):
            self.ping(second)
        self.assertEqual(self.ping(201, observed=False).state, "SUSPECT")
        self.assertEqual(self.assess(290).state, "SUSPECT")
        self.assertEqual(self.assess(291).state, "UNHEALTHY")

    def test_revoked_session_cannot_report_or_keep_station_healthy(self):
        self.ping(0)
        StaffSession.objects.filter(pk=self.session.pk).update(revoked_at=self.now)
        self.assertEqual(self.assess(1).state, "SUSPECT")
        with self.assertRaises(PermissionDenied):
            self.ping(2)

    def test_station_permission_and_device_membership_provenance(self):
        self.membership.role = "STAFF"
        self.membership.save()
        with self.assertRaises(PermissionDenied):
            self.ping(0)

        self.membership.role = "MANAGER"
        self.membership.save()
        other = Venue.objects.create(name="Other", slug="other-kds")
        DeviceRegistration.objects.filter(pk=self.session.device_id).update(venue=other)
        with self.assertRaises(PermissionDenied):
            self.ping(0)

    def test_revocation_cannot_erase_previous_missing_boundary(self):
        self.ping(0)
        StaffSession.objects.filter(pk=self.session.pk).update(revoked_at=self.now + timedelta(seconds=1))
        self.assertEqual(self.assess(120).state, "UNHEALTHY")

    def test_api_identity_and_client_clock_are_not_accepted(self):
        public = APIClient()
        self.assertEqual(public.post("/printing/kds/BAR/heartbeat/", {"queue_observed": True}, format="json").status_code, 401)
        client = APIClient()
        client.force_authenticate(user=self.staff, token=self.session)
        response = client.post("/printing/kds/BAR/heartbeat/", {"queue_observed": True, "seen_at": "2099-01-01", "device_id": str(self.session.device_id)}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(KdsDeviceHeartbeat.objects.count(), 0)
        response = client.post("/printing/kds/BAR/heartbeat/", {"queue_observed": True}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["auto_fallback_enabled"])

    def test_version_conflict_preserves_detector_policy_and_audit(self):
        actor = ActorContext.from_session(self.session)
        values = dict(actor=actor, station="BAR", expected_version=1, reason="Observe kitchen timing", heartbeat_ttl_seconds=30, failure_threshold_seconds=120, recovery_threshold_seconds=60)
        row = configure_detector(**values)
        self.assertEqual(row.version, 2)
        with self.assertRaises(APIException) as raised:
            configure_detector(**values)
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(AuditEvent.objects.filter(event_type="print.kds_detector_configured").count(), 1)
        row.refresh_from_db()
        self.assertEqual(row.failure_threshold_seconds, 120)


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks")
class KdsConcurrencyTests(KdsFixture, TransactionTestCase):
    def test_two_managers_same_version_one_update_and_one_conflict(self):
        assess_station(venue_id=self.venue.id, station="BAR")
        actor = ActorContext.from_session(self.session)
        barrier = Barrier(2)

        def worker(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    configure_detector(
                        actor=actor, station="BAR", expected_version=1,
                        reason="Concurrent manager update", heartbeat_ttl_seconds=30,
                        failure_threshold_seconds=90 + index,
                        recovery_threshold_seconds=60,
                    )
                    return 200
                except APIException as error:
                    return error.status_code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, (0, 1)))
        self.assertCountEqual(results, [200, 409])
        self.assertEqual(KdsStationHealth.objects.get().version, 2)
        self.assertEqual(AuditEvent.objects.filter(event_type="print.kds_detector_configured").count(), 1)

    def test_simultaneous_heartbeat_and_repeated_checks_one_station_row(self):
        barrier = Barrier(2)

        def worker(_):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return heartbeat(session_id=self.session.id, station="BAR", queue_observed=True).pk
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(worker, (0, 1)))
        self.assertEqual(ids[0], ids[1])
        for _ in range(100):
            assess_station(venue_id=self.venue.id, station="BAR")
        self.assertEqual(KdsStationHealth.objects.count(), 1)
        self.assertEqual(KdsDeviceHeartbeat.objects.count(), 1)
        self.assertEqual(PrintJob.objects.count(), 0)
