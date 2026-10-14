from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.access.context import ActorContext
from modules.access.models import StaffSession
from modules.audit.models import AuditEvent
from modules.catalog.availability import AvailabilityError, execute_availability
from modules.catalog.models import AvailabilityCommand, Product
from modules.ledger.models import Charge, Payment
from modules.ordering.models import OrderItem
from tests.test_production_batches import BatchFixture


class AvailabilityFixture(BatchFixture):
    def setUp(self):
        super().setUp()
        self.command = {"product_id": self.product.pk, "state": "UNAVAILABLE", "expected_version": 1, "idempotency_key": "availability-1", "reason": "Esgotado"}

    def execute(self, payload=None, actor=None):
        return execute_availability(actor=actor or self.actor, **(payload or self.command))

    def other_actor(self):
        session = StaffSession.objects.create(venue=self.venue, staff_member=self.staff,
            membership=self.membership, expires_at=timezone.now() + timedelta(hours=1))
        return ActorContext(self.venue.pk, self.staff.pk, session.pk, None)


class AvailabilityCommandTests(AvailabilityFixture, TestCase):
    def test_replay_after_later_change_preserves_original_receipt_history_and_money(self):
        from modules.ledger.services import collect_payment
        collect_payment(tab_id=self.tab.pk, amount_cents=100, method="EXTERNAL_TERMINAL", idempotency_key="test-payment", actor=self.actor)
        money = (list(Charge.objects.values()), list(Payment.objects.values()))
        items = list(OrderItem.objects.values())
        receipt = self.execute()
        self.assertTrue(receipt["changed"])
        self.execute({**self.command, "state": "AVAILABLE", "expected_version": 2, "idempotency_key": "later"})
        before = list(AuditEvent.objects.values())
        self.assertEqual(self.execute(), receipt)
        self.product.availability.refresh_from_db()
        self.assertEqual((self.product.availability.state, self.product.availability.version), ("AVAILABLE", 3))
        self.assertEqual(list(AuditEvent.objects.values()), before)
        self.assertEqual((list(Charge.objects.values()), list(Payment.objects.values())), money)
        self.assertEqual(list(OrderItem.objects.values()), items)
        self.product.refresh_from_db()
        self.assertTrue(self.product.active)
        event = AuditEvent.objects.get(event_type="product.availability_changed", metadata__command_id=receipt["command_id"])
        self.assertEqual(event.actor_staff_id, self.staff.pk)
        self.assertEqual(event.actor_session_id, self.session.pk)
        self.assertEqual(event.metadata["reason"], "Esgotado")
        self.assertEqual((event.metadata["before_version"], event.metadata["after_version"]), (1, 2))

    def test_rejected_version_replays_without_state_or_timestamp_change(self):
        before = self.product.availability.changed_at
        rejected = self.execute({**self.command, "expected_version": 9})
        self.assertEqual(rejected["status"], "REJECTED")
        self.assertEqual(rejected["conflicts"], ["VERSION_CONFLICT"])
        self.product.availability.refresh_from_db()
        self.assertEqual(self.product.availability.changed_at, before)
        self.execute({**self.command, "idempotency_key": "valid-change"})
        self.assertEqual(self.execute({**self.command, "expected_version": 9, "idempotency_key": "rejected"})["status"], "REJECTED")
        self.product.availability.refresh_from_db()
        changed_at = self.product.availability.changed_at
        self.assertEqual(self.execute({**self.command, "expected_version": 9}), rejected)
        self.product.availability.refresh_from_db()
        self.assertEqual(self.product.availability.changed_at, changed_at)

    def test_changed_payload_or_product_cannot_reuse_key(self):
        self.execute()
        other = Product.objects.create(venue=self.venue, name="Other product", price_cents=100, fulfillment_station="BAR")
        for changed in [{"state": "AVAILABLE"}, {"reason": "Outro motivo"}, {"product_id": other.pk}, {"expected_version": 2}]:
            with self.subTest(changed=changed), self.assertRaises(AvailabilityError) as error:
                self.execute({**self.command, **changed})
            self.assertEqual(error.exception.code, "IDEMPOTENCY_CONFLICT")
        self.assertEqual(AvailabilityCommand.objects.count(), 1)

    def test_noop_records_command_without_fake_change(self):
        before = self.product.availability.changed_at
        receipt = self.execute({**self.command, "state": "AVAILABLE"})
        self.assertEqual((receipt["status"], receipt["changed"], receipt["version"]), ("APPLIED", False, 1))
        self.product.availability.refresh_from_db()
        self.assertEqual(self.product.availability.changed_at, before)
        self.assertEqual(AuditEvent.objects.filter(event_type="product.availability_changed").count(), 0)
        self.assertEqual(AuditEvent.objects.filter(event_type="product.availability_command.completed").count(), 1)

    def test_audit_failure_rolls_back_command_and_availability(self):
        with patch("modules.catalog.availability.record_audit_event", side_effect=RuntimeError("Test audit failure")), self.assertRaises(RuntimeError):
            self.execute()
        self.product.availability.refresh_from_db()
        self.assertEqual((self.product.availability.state, self.product.availability.version), ("AVAILABLE", 1))
        self.assertEqual(AvailabilityCommand.objects.count(), 0)
        self.assertEqual(self.execute()["status"], "APPLIED")

    def test_session_capability_and_venue_revalidated_before_replay(self):
        self.execute()
        actor = self.other_actor()
        self.assertEqual(self.execute(actor=actor)["status"], "REJECTED")
        self.membership.capability_overrides = {"deny": ["catalog.availability.manage_station"]}
        self.membership.save()
        with self.assertRaises(AvailabilityError):
            self.execute()
        self.session.revoked_at = timezone.now()
        self.session.save()
        with self.assertRaises(AvailabilityError) as error:
            self.execute()
        self.assertEqual(error.exception.code, "SESSION_INVALID")
        from modules.venue.models import Venue
        foreign = Product.objects.create(venue=Venue.objects.create(name="Other venue", slug="other-availability"), name="Foreign", price_cents=100, fulfillment_station="BAR")
        self.membership.capability_overrides = {}
        self.membership.save()
        with self.assertRaises(AvailabilityError) as error:
            self.execute({**self.command, "product_id": foreign.pk, "idempotency_key": "foreign"}, actor=actor)
        self.assertEqual(error.exception.code, "PRODUCT_NOT_FOUND")

    def test_api_optin_validation_legacy_and_catalog_version(self):
        client = APIClient()
        path = f"/catalog/products/{self.product.pk}/availability/"
        self.assertIn(client.post(path, {"state": "UNAVAILABLE"}, format="json").status_code, (401, 403))
        login = client.post("/auth/login/", {"venue_slug": self.venue.slug, "login_identifier": self.staff.login_identifier,
            "pin": "2468", "installation_id": "availability-api-test", "platform": "WEB"}, format="json")
        client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
        self.assertEqual(client.get("/catalog/products/").json()["results"][0]["availability_version"], 1)
        for data in [{"state": "UNAVAILABLE", "idempotency_key": "x"}, {"state": "UNAVAILABLE", "expected_version": 1},
                     {"state": "UNAVAILABLE", "expected_version": True, "idempotency_key": "x"},
                     {"state": "UNAVAILABLE", "expected_version": 1, "idempotency_key": " "},
                     {"state": "UNAVAILABLE", "expected_version": 1, "idempotency_key": "x", "reason": "x" * 601}]:
            self.assertEqual(client.post(path, data, format="json").status_code, 400)
        payload = {k: v for k, v in self.command.items() if k != "product_id"}
        response = client.post(path, payload, format="json")
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(client.post(path, payload, format="json").json(), response.json())
        self.assertEqual(client.post(path, {**payload, "idempotency_key": "stale"}, format="json").status_code, 409)
        legacy = client.post(path, {"state": "AVAILABLE"}, format="json")
        self.assertEqual(legacy.status_code, 200)
        self.assertEqual(legacy.json()["version"], 3)


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL locks")
class AvailabilityConcurrencyTests(AvailabilityFixture, TransactionTestCase):
    def race(self, payloads, actors=None):
        barrier = Barrier(2)
        def worker(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    return self.execute(payloads[index], actor=actors[index] if actors else None)
                except AvailabilityError as error:
                    return error.code
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(worker, range(2)))

    def test_same_key_one_effect(self):
        results = self.race([self.command, self.command])
        self.assertEqual(results[0], results[1])
        self.assertEqual(AvailabilityCommand.objects.count(), 1)
        self.assertEqual(AuditEvent.objects.filter(event_type="product.availability_changed").count(), 1)

    def test_changed_same_key_conflicts(self):
        results = self.race([self.command, {**self.command, "reason": "Outro"}])
        self.assertIn("IDEMPOTENCY_CONFLICT", results)
        self.assertEqual(AvailabilityCommand.objects.count(), 1)

    def test_other_session_same_product_one_version_wins(self):
        results = self.race([self.command, self.command], [self.actor, self.other_actor()])
        self.assertEqual(sorted(row["status"] for row in results), ["APPLIED", "REJECTED"])
        self.assertEqual(AuditEvent.objects.filter(event_type="product.availability_changed").count(), 1)

    def test_distinct_products_same_session_both_apply(self):
        other = Product.objects.create(venue=self.venue, name="Independent availability", price_cents=100, fulfillment_station="BAR")
        results = self.race([self.command, {**self.command, "product_id": other.pk, "idempotency_key": "other"}])
        self.assertEqual([row["status"] for row in results], ["APPLIED", "APPLIED"])
