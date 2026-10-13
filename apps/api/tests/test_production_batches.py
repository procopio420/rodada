import copy
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
from modules.access.models import StaffMember, StaffSession, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.catalog.models import Product, ProductAvailability
from modules.dispatch.models import DispatchTask
from modules.ledger.models import Charge, Payment
from modules.ordering.models import OrderItem, ProductionBatch, Tab
from modules.ordering.production import execute_production_batch, snapshot_fingerprint
from modules.ordering.services import OrderingServiceError, confirm_order, transition_order_item
from modules.venue.models import Venue


class BatchFixture:
    def setUp(self):
        self.venue = Venue.objects.create(name="Batch test", slug="batch-test")
        self.staff = StaffMember.objects.create(display_name="Operator", login_identifier="batch-test")
        self.staff.set_pin("2468")
        self.staff.save()
        self.membership = VenueStaffMembership.objects.create(
            venue=self.venue, staff_member=self.staff, role="MANAGER")
        self.session = StaffSession.objects.create(
            venue=self.venue, staff_member=self.staff, membership=self.membership,
            expires_at=timezone.now() + timedelta(hours=1))
        self.actor = ActorContext(self.venue.pk, self.staff.pk, self.session.pk, None)
        self.tab = Tab.objects.create(venue=self.venue)
        self.product = Product.objects.create(venue=self.venue, name="Batch item", price_cents=100,
                                              fulfillment_station="KITCHEN")
        order = confirm_order(tab_id=self.tab.pk, source="STAFF", actor=self.actor,
                              idempotency_key="initial-order", lines=[
                                  {"product_id": self.product.pk, "quantity": 2},
                                  {"product_id": self.product.pk, "quantity": 1}])
        self.items = list(order.items.order_by("id"))
        self.payload = {"idempotency_key": "batch-1", "station": "KITCHEN",
                        "target_state": "PREPARING", "lines": self.lines()}

    def lines(self):
        return [{"item_id": str(item.pk), "expected_state": item.state,
                 "quantity": item.remaining_quantity,
                 "snapshot_fingerprint": snapshot_fingerprint(item.customization_snapshot)}
                for item in self.items]

    def execute(self, payload=None, actor=None):
        return execute_production_batch(actor=actor or self.actor, **(payload or self.payload))

    def states(self):
        return list(OrderItem.objects.order_by("id").values_list("state", flat=True))


class ProductionBatchTests(BatchFixture, TestCase):
    def test_preparing_then_ready_replay_audit_dispatch_and_money_preserved(self):
        from modules.ledger.services import collect_payment
        collect_payment(tab_id=self.tab.pk, amount_cents=100, method="EXTERNAL_TERMINAL",
                        idempotency_key="test-receipt", actor=self.actor)
        money = (list(Charge.objects.values()), list(Payment.objects.values()))
        snapshots = list(OrderItem.objects.order_by("id").values_list("customization_snapshot", flat=True))
        receipt = self.execute()
        self.assertEqual(receipt["status"], "APPLIED")
        self.assertEqual(self.execute(), receipt)
        for item in self.items:
            item.refresh_from_db()
        timestamps = [item.preparing_at for item in self.items]
        self.payload.update(idempotency_key="batch-ready", target_state="READY", lines=self.lines())
        ready = self.execute()
        self.assertEqual(self.execute(), ready)
        self.assertEqual(DispatchTask.objects.count(), 2)
        self.assertEqual(AuditEvent.objects.filter(event_type="production_batch.completed").count(), 2)
        transitions = AuditEvent.objects.filter(event_type="order_item.transitioned")
        self.assertEqual(transitions.count(), 4)
        self.assertTrue(all(event.actor_session_id == self.session.pk and
                            event.metadata["command_id"] in (receipt["command_id"], ready["command_id"])
                            for event in transitions))
        self.assertEqual(money, (list(Charge.objects.values()), list(Payment.objects.values())))
        self.assertEqual(snapshots, list(OrderItem.objects.order_by("id").values_list("customization_snapshot", flat=True)))
        self.assertEqual(timestamps, list(OrderItem.objects.order_by("id").values_list("preparing_at", flat=True)))

    def test_mixed_waiting_origins_and_current_unavailability_are_compatible(self):
        transition_order_item(item_id=self.items[0].pk, target_state="ACCEPTED", actor=self.actor)
        self.items[0].refresh_from_db()
        self.payload["lines"] = self.lines()
        ProductAvailability.objects.filter(product=self.product).update(state="UNAVAILABLE")
        self.product.price_cents = 200
        self.product.save(update_fields=["price_cents"])
        self.assertEqual(self.execute()["status"], "APPLIED")
        self.assertEqual(self.states(), ["PREPARING", "PREPARING"])

    def test_each_stale_precondition_rejects_all_and_replays_rejection(self):
        for field, value, reason in [("expected_state", "PREPARING", "STATE_CONFLICT"),
                                     ("quantity", 99, "QUANTITY_CONFLICT"),
                                     ("snapshot_fingerprint", "0" * 64, "SNAPSHOT_CONFLICT")]:
            with self.subTest(field=field):
                payload = copy.deepcopy(self.payload)
                payload["idempotency_key"] = field
                payload["lines"][0][field] = value
                receipt = self.execute(payload)
                self.assertEqual(receipt["status"], "REJECTED")
                self.assertIn(reason, receipt["lines"][0]["conflicts"])
                self.assertTrue(all(line["status"] == "NOT_APPLIED" for line in receipt["lines"]))
                self.assertEqual(self.execute(payload), receipt)
                self.assertEqual(self.states(), ["NEW", "NEW"])
        self.assertFalse(AuditEvent.objects.filter(event_type="order_item.transitioned").exists())

    def test_changed_payload_conflicts_without_replacing_receipt(self):
        receipt = self.execute()
        changed = copy.deepcopy(self.payload)
        changed["lines"][0]["quantity"] = 50
        with self.assertRaises(OrderingServiceError) as error:
            self.execute(changed)
        self.assertEqual(error.exception.code, "IDEMPOTENCY_CONFLICT")
        self.assertEqual(self.execute(), receipt)
        self.assertEqual(ProductionBatch.objects.count(), 1)

    def test_configuration_note_variant_modifier_and_legacy_must_not_mix(self):
        original = copy.deepcopy(self.items[0].customization_snapshot)
        changed_values = [None, {**original, "special_instructions": "Separate"},
                          {**original, "variant": {"id": "variant-test", "name": "Other"}},
                          {**original, "modifiers": [{"option_id": "option-test", "group_id": "group-test",
                            "name": "Extra", "group_name": "Extras", "semantic_kind": "ADD"}]},
                          {**original, "operational_extra": "Separate"}]
        for index, snapshot in enumerate(changed_values):
            with self.subTest(index=index):
                # Simulate historical/imported records, not a product mutation endpoint.
                OrderItem.objects.filter(pk=self.items[0].pk).update(customization_snapshot=snapshot or {})
                self.items[0].refresh_from_db()
                payload = {**self.payload, "idempotency_key": f"config-{index}", "lines": self.lines()}
                self.assertEqual(self.execute(payload)["status"], "REJECTED")
                self.assertEqual(self.states(), ["NEW", "NEW"])

    def test_money_does_not_split_configuration(self):
        snapshot = copy.deepcopy(self.items[0].customization_snapshot)
        snapshot.update(base_price_cents=999, unit_price_cents=999, line_total_cents=999)
        OrderItem.objects.filter(pk=self.items[0].pk).update(customization_snapshot=snapshot)
        self.items[0].refresh_from_db()
        self.payload["lines"] = self.lines()
        self.assertEqual(self.execute()["status"], "APPLIED")

    def test_modifier_order_and_line_order_replay_are_equivalent(self):
        options = [{"option_id": str(index), "group_id": "group-test", "name": f"Extra {index}",
                    "group_name": "Extras", "semantic_kind": "ADD", "price_delta_cents": index}
                   for index in (1, 2)]
        for index, item in enumerate(self.items):
            snapshot = copy.deepcopy(item.customization_snapshot)
            snapshot["modifiers"] = options if index == 0 else list(reversed(options))
            OrderItem.objects.filter(pk=item.pk).update(customization_snapshot=snapshot)
            item.refresh_from_db()
        self.payload["lines"] = self.lines()
        receipt = self.execute()
        self.assertEqual(receipt["status"], "APPLIED")
        reversed_payload = {**self.payload, "lines": list(reversed(self.payload["lines"]))}
        self.assertEqual(self.execute(reversed_payload), receipt)

    def test_wrong_station_and_other_venue_reject_without_disclosing_item(self):
        self.payload["station"] = "BAR"
        self.assertEqual(self.execute()["status"], "REJECTED")
        other = Venue.objects.create(name="Other venue", slug="batch-other")
        Tab.objects.filter(pk=self.tab.pk).update(venue=other)
        self.payload.update(station="KITCHEN", idempotency_key="other-venue")
        receipt = self.execute()
        self.assertTrue(all(line["conflicts"] == ["ITEM_NOT_FOUND"] for line in receipt["lines"]))
        self.assertEqual(self.states(), ["NEW", "NEW"])

    def test_cancelled_quantity_prevents_stale_batch(self):
        from modules.corrections.services import cancel_before_fulfillment
        from modules.ledger.services import reverse_open_responsibility
        partial_item = next(item for item in self.items if item.quantity == 2)
        cancel_before_fulfillment(item_id=partial_item.pk, actor=self.actor, kind="CANCEL_ITEM",
            reason_code="WRONG_ENTRY", reason_text="", financial_reversal_hook=reverse_open_responsibility,
            idempotency_key="batch-cancel", quantity=1)
        self.assertEqual(self.execute()["status"], "REJECTED")
        self.assertEqual(self.states(), ["NEW", "NEW"])
        partial_item.refresh_from_db()
        self.payload.update(idempotency_key="fresh-quantity", lines=self.lines())
        self.assertEqual(self.execute()["status"], "APPLIED")

    def test_dispatch_failure_rolls_back_all_lines_command_and_audit_then_retry_succeeds(self):
        self.execute()
        for item in self.items:
            item.refresh_from_db()
        self.payload.update(idempotency_key="ready-failure", target_state="READY", lines=self.lines())
        from modules.dispatch.services import ensure_delivery_task_for_ready_order_item
        calls = []
        def fail_second(**kwargs):
            calls.append(kwargs)
            if len(calls) == 2:
                raise RuntimeError("Injected test failure")
            return ensure_delivery_task_for_ready_order_item(**kwargs)
        audit_count = AuditEvent.objects.count()
        with patch("modules.dispatch.services.ensure_delivery_task_for_ready_order_item", side_effect=fail_second), self.assertRaises(RuntimeError):
            self.execute()
        self.assertEqual(self.states(), ["PREPARING", "PREPARING"])
        self.assertFalse(OrderItem.objects.exclude(ready_at=None).exists())
        self.assertEqual(ProductionBatch.objects.count(), 1)
        self.assertEqual(AuditEvent.objects.count(), audit_count)
        self.assertEqual(DispatchTask.objects.count(), 0)
        self.assertEqual(self.execute()["status"], "APPLIED")
        self.assertEqual(DispatchTask.objects.count(), 2)

    def test_new_session_cannot_replay_original_command_or_revoked_session_execute(self):
        receipt = self.execute()
        new_session = StaffSession.objects.create(venue=self.venue, staff_member=self.staff,
            membership=self.membership, expires_at=timezone.now() + timedelta(hours=1))
        actor = ActorContext(self.venue.pk, self.staff.pk, new_session.pk, None)
        self.assertEqual(self.execute(actor=actor)["status"], "REJECTED")
        self.assertEqual(self.execute(), receipt)
        self.session.revoked_at = timezone.now()
        self.session.save(update_fields=["revoked_at"])
        with self.assertRaises(OrderingServiceError) as error:
            self.execute()
        self.assertEqual(error.exception.code, "SESSION_INVALID")

    def test_api_validation_capability_and_queue_fingerprint(self):
        client = APIClient()
        self.assertIn(client.post("/production/batches/", self.payload, format="json").status_code, (401, 403))
        login = client.post("/auth/login/", {"venue_slug": self.venue.slug,
            "login_identifier": self.staff.login_identifier, "pin": "2468",
            "installation_id": "batch-api-test", "platform": "WEB"}, format="json")
        client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
        queue = client.get("/production/KITCHEN/").json()["results"]
        self.assertTrue(all(row["snapshot_fingerprint"] == snapshot_fingerprint(row["customization_snapshot"]) for row in queue))
        for lines in [[], self.payload["lines"] * 2, self.payload["lines"] * 26]:
            self.assertEqual(client.post("/production/batches/", {**self.payload, "lines": lines}, format="json").status_code, 400)
        receipt = client.post("/production/batches/", self.payload, format="json")
        self.assertEqual(receipt.status_code, 200, receipt.json())
        self.assertEqual(client.post("/production/batches/", self.payload, format="json").json(), receipt.json())
        rejected = client.post("/production/batches/", {**self.payload, "idempotency_key": "api-stale"}, format="json")
        self.assertEqual(rejected.status_code, 409)
        self.assertEqual(rejected.json()["status"], "REJECTED")
        self.membership.capability_overrides = {"deny": ["order.confirm"]}
        self.membership.save(update_fields=["capability_overrides"])
        self.assertEqual(client.post("/production/batches/", self.payload, format="json").status_code, 403)
        self.membership.status = "SUSPENDED"
        self.membership.save(update_fields=["status"])
        self.assertIn(client.post("/production/batches/", self.payload, format="json").status_code, (401, 403))


@skipUnless(connection.vendor == "postgresql", "Requires real PostgreSQL locks")
class ProductionBatchConcurrencyTests(BatchFixture, TransactionTestCase):
    def race(self, payloads, actors=None):
        barrier = Barrier(2)
        def worker(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    return self.execute(payloads[index], actor=actors[index] if actors else None)
                except OrderingServiceError as error:
                    return error.code
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(worker, range(2)))

    def test_same_key_concurrent_replay_has_single_effect(self):
        results = self.race([self.payload, self.payload])
        self.assertEqual(results[0], results[1])
        self.assertEqual(ProductionBatch.objects.count(), 1)
        self.assertEqual(AuditEvent.objects.filter(event_type="order_item.transitioned").count(), 2)

    def test_changed_same_key_has_one_conflict(self):
        changed = copy.deepcopy(self.payload)
        changed["lines"][0]["quantity"] = 50
        results = self.race([self.payload, changed])
        self.assertIn("IDEMPOTENCY_CONFLICT", results)
        self.assertEqual(ProductionBatch.objects.count(), 1)

    def test_overlapping_batches_different_sessions_apply_only_one(self):
        session = StaffSession.objects.create(venue=self.venue, staff_member=self.staff,
            membership=self.membership, expires_at=timezone.now() + timedelta(hours=1))
        actor = ActorContext(self.venue.pk, self.staff.pk, session.pk, None)
        results = self.race([self.payload, {**self.payload, "idempotency_key": "overlap"}], [self.actor, actor])
        self.assertEqual(sorted(result["status"] for result in results), ["APPLIED", "REJECTED"])
        self.assertEqual(AuditEvent.objects.filter(event_type="order_item.transitioned").count(), 2)

    def test_two_tabs_reverse_selection_order_different_sessions_do_not_deadlock(self):
        other_tab = Tab.objects.create(venue=self.venue)
        order = confirm_order(tab_id=other_tab.pk, source="STAFF", actor=self.actor,
            idempotency_key="second-tab-order", lines=[{"product_id": self.product.pk, "quantity": 1}])
        self.items.append(order.items.get())
        self.payload["lines"] = self.lines()
        session = StaffSession.objects.create(venue=self.venue, staff_member=self.staff,
            membership=self.membership, expires_at=timezone.now() + timedelta(hours=1))
        actor = ActorContext(self.venue.pk, self.staff.pk, session.pk, None)
        reverse = {**self.payload, "idempotency_key": "reverse-selection",
                   "lines": list(reversed(self.payload["lines"]))}
        results = self.race([self.payload, reverse], [self.actor, actor])
        self.assertEqual(sorted(result["status"] for result in results), ["APPLIED", "REJECTED"])
        self.assertEqual(AuditEvent.objects.filter(event_type="order_item.transitioned").count(), 3)

    def test_batch_racing_partial_cancellation_preserves_consistent_scope(self):
        from modules.corrections.services import CorrectionServiceError, cancel_before_fulfillment
        from modules.ledger.services import reverse_open_responsibility, totals
        partial_item = next(item for item in self.items if item.quantity == 2)
        barrier = Barrier(2)
        def worker(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                if index == 0:
                    return self.execute()["status"]
                try:
                    cancel_before_fulfillment(item_id=partial_item.pk, actor=self.actor, kind="CANCEL_ITEM",
                        reason_code="WRONG_ENTRY", reason_text="", idempotency_key="concurrent-cancel",
                        financial_reversal_hook=reverse_open_responsibility, quantity=1)
                    return "CANCELLED_QUANTITY"
                except CorrectionServiceError as error:
                    return error.code
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, range(2)))
        partial_item.refresh_from_db()
        if results[0] == "APPLIED":
            self.assertEqual(results[1], "CORRECTION_STAGE_REQUIRES_APPROVAL")
            self.assertEqual(self.states(), ["PREPARING", "PREPARING"])
            self.assertEqual(totals(self.tab)["exposure_cents"], 300)
        else:
            self.assertEqual(results, ["REJECTED", "CANCELLED_QUANTITY"])
            self.assertEqual(self.states(), ["NEW", "NEW"])
            self.assertEqual(partial_item.remaining_quantity, partial_item.quantity - 1)
            self.assertEqual(totals(self.tab)["exposure_cents"], 200)
        self.assertFalse(Payment.objects.exists())
