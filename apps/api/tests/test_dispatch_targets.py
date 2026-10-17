"""Spec033 E01-02/E03-02/03: exact targets, never account identity by label."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.utils import timezone
from rest_framework.test import APIClient

from modules.audit.models import AuditEvent
from modules.dispatch.models import DispatchTask
from modules.dispatch.services import (
    create_service_request,
    ensure_delivery_task_for_ready_order_item,
)
from modules.dispatch.targets import StaffTargets, staff_tasks
from modules.guest_access.models import GuestSession
from modules.guest_access.services import create_or_get_guest_tab, resolve_table_qr
from modules.hospitality.models import Table, TableOccupancy, TabOccupancyAssignment
from modules.ordering.models import Tab
from tests import test_dispatch as foundation


class DispatchTargetTests(TestCase):
    setUp = foundation.DispatchFoundationTests.setUp
    ready_item = foundation.DispatchFoundationTests.ready_item

    def visit(self):
        table = Table.objects.create(
            venue=self.venue, label="08", status="OCCUPIED", guest_ordering_mode="JOIN_ACTIVE",
        )
        occupancy = TableOccupancy.objects.create(table=table, generation=table.access_generation)
        return table, occupancy

    def call(self, table, *, with_tab=True, task_type="BILL_REQUEST"):
        guest = resolve_table_qr(public_token=table.public_token)
        if with_tab:
            create_or_get_guest_tab(session_token=guest.token, display_label="Mesmo nome")
        task = create_service_request(
            request_id=uuid.uuid4(), task_type=task_type, session_token=guest.token,
        )
        return task, guest

    def detail(self, task):
        response = self.client.get(f"/dispatch/tasks/{task.id}/")
        assert response.status_code == 200, response.json()
        assert response.json()["target_version"] == 1
        return response.json()

    def test_two_guest_accounts_same_table_have_exact_distinct_targets_and_no_read_mutation(self):
        table, occupancy = self.visit()
        first, _ = self.call(table, task_type="SERVICE_REQUEST")
        second, _ = self.call(table)
        assert first.requested_tab_id != second.requested_tab_id
        audits = AuditEvent.objects.count()
        for task in (first, second):
            target = self.detail(task)["target"]
            assert target == {
                "kind": "TAB", "tab_id": str(task.requested_tab_id), "table_id": str(table.id),
                "occupancy_id": str(occupancy.id), "generation": table.access_generation,
            }
            task.refresh_from_db()
            assert task.state == "OPEN" and task.claimed_by_id is None
        assert AuditEvent.objects.count() == audits
        rows = self.client.get("/dispatch/requests/").json()["results"]
        assert {row["target"]["tab_id"] for row in rows} == {
            str(first.requested_tab_id), str(second.requested_tab_id),
        }

    def test_legacy_or_unbound_request_never_guesses_the_only_account(self):
        table, occupancy = self.visit()
        self.call(table)
        unbound, _ = self.call(table, with_tab=False)
        legacy = DispatchTask.objects.create(
            venue=self.venue, task_type="SERVICE_REQUEST",
            destination_table=table, destination_occupancy=occupancy, destination_label="Mesa 08",
        )
        for task in (unbound, legacy):
            target = self.detail(task)["target"]
            assert target["kind"] == "TABLE" and target["tab_id"] is None
            assert target["occupancy_id"] == str(occupancy.id)

    def test_revoked_expired_or_reassigned_session_cannot_route_to_account(self):
        table, _ = self.visit()
        for change in (
            {"revoked_at": timezone.now()},
            {"expires_at": timezone.now() - timedelta(seconds=1)},
            {"tab": Tab.objects.create(venue=self.venue)},
        ):
            task, guest = self.call(table)
            GuestSession.objects.filter(pk=guest.session.id).update(**change)
            target = self.detail(task)["target"]
            assert target["kind"] == "TABLE" and target["tab_id"] is None

    def test_release_and_old_generation_do_not_route_into_next_visit(self):
        table, occupancy = self.visit()
        task, _ = self.call(table)
        occupancy.released_at = timezone.now()
        occupancy.save(update_fields=["released_at"])
        assert self.detail(task)["target"]["kind"] == "UNAVAILABLE"
        occupancy.released_at = None
        occupancy.save(update_fields=["released_at"])
        table.access_generation += 1
        table.save(update_fields=["access_generation"])
        assert self.detail(task)["target"]["kind"] == "UNAVAILABLE"

    def test_moved_account_falls_back_to_original_active_table_without_retargeting(self):
        table, occupancy = self.visit()
        task, _ = self.call(table)
        TabOccupancyAssignment.objects.filter(tab_id=task.requested_tab_id).update(released_at=timezone.now())
        other = Table.objects.create(venue=self.venue, label="09", status="OCCUPIED")
        moved = TableOccupancy.objects.create(table=other, generation=other.access_generation)
        TabOccupancyAssignment.objects.create(tab_id=task.requested_tab_id, occupancy=moved)
        target = self.detail(task)["target"]
        assert target["kind"] == "TABLE" and target["tab_id"] is None
        assert target["occupancy_id"] == str(occupancy.id)

    def test_delivery_has_canonical_item_order_station_and_survives_financial_close(self):
        tab = Tab.objects.create(venue=self.venue, state="CLOSED")
        item = self.ready_item(tab=tab)
        # Production routing must be an immutable confirmed snapshot.
        type(item).objects.filter(pk=item.id).update(fulfillment_station_snapshot="BAR")
        task = ensure_delivery_task_for_ready_order_item(item_id=item.id, actor=self.actor)
        item.product.fulfillment_station = "KITCHEN"
        item.product.save(update_fields=["fulfillment_station"])
        payload = self.detail(task)
        assert payload["target"] == {
            "kind": "TAB", "tab_id": str(tab.id), "table_id": None,
            "occupancy_id": None, "generation": None,
        }
        assert payload["order_id"] == str(item.order_id)
        assert payload["order_item_id"] == str(item.id)
        assert payload["fulfillment_station"] == "BAR"
        assert payload["item_state"] == "READY"
        assert self.client.get("/dispatch/delivery/").json()["results"][0]["target"] == payload["target"]

    def test_delivery_legacy_station_is_unknown_not_current_product_routing(self):
        item = self.ready_item()
        task = ensure_delivery_task_for_ready_order_item(item_id=item.id, actor=self.actor)
        assert self.detail(task)["fulfillment_station"] is None

    def test_delivery_target_tracks_valid_current_assignment_not_snapshot(self):
        table, occupancy = self.visit()
        tab = Tab.objects.create(venue=self.venue)
        assignment = TabOccupancyAssignment.objects.create(tab=tab, occupancy=occupancy)
        task = ensure_delivery_task_for_ready_order_item(item_id=self.ready_item(tab=tab).id, actor=self.actor)
        assert self.detail(task)["target"]["table_id"] == str(table.id)
        assignment.released_at = timezone.now()
        assignment.save(update_fields=["released_at"])
        other = Table.objects.create(venue=self.venue, label="Moved", status="OCCUPIED")
        destination = TableOccupancy.objects.create(table=other, generation=other.access_generation)
        TabOccupancyAssignment.objects.create(tab=tab, occupancy=destination)
        assert self.detail(task)["target"]["table_id"] == str(other.id)
        other.access_generation += 1
        other.save(update_fields=["access_generation"])
        assert self.detail(task)["target"]["table_id"] is None

    def test_foreign_task_and_revoked_staff_cannot_read_exact_task(self):
        foreign = DispatchTask.objects.create(venue=self.other_venue, task_type="SERVICE_REQUEST")
        assert self.client.get(f"/dispatch/tasks/{foreign.id}/").status_code == 404
        table, _ = self.visit()
        task, _ = self.call(table)
        assert APIClient().get(f"/dispatch/tasks/{task.id}/").status_code == 401
        from modules.access.models import StaffSession
        StaffSession.objects.filter(pk=self.actor.session_id).update(revoked_at=timezone.now())
        assert self.client.get(f"/dispatch/tasks/{task.id}/").status_code == 401

    def test_guest_response_never_exposes_staff_target_or_session_provenance(self):
        table, _ = self.visit()
        guest = resolve_table_qr(public_token=table.public_token)
        client = APIClient()
        client.credentials(HTTP_X_GUEST_SESSION=guest.token)
        response = client.post("/guest/service-requests/", {
            "request_id": str(uuid.uuid4()), "task_type": "BILL_REQUEST",
        }, format="json")
        assert response.status_code == 201
        assert set(response.json()) == {"id", "task_type", "state"}
        payload = self.detail(DispatchTask.objects.get(pk=response.json()["id"]))
        assert "requesting_guest_session" not in str(payload)
        assert guest.token not in str(payload)

    def test_detail_keeps_rival_claim_and_returns_current_ownership(self):
        from modules.access.models import StaffMember
        from modules.hospitality.models import Zone
        table, _ = self.visit()
        zone = Zone.objects.create(venue=self.venue, label="Rua")
        table.zone = zone
        table.save(update_fields=["zone"])
        task, _ = self.call(table)
        other = StaffMember.objects.create(display_name="Outro", login_identifier="other-target")
        DispatchTask.objects.filter(pk=task.id).update(state="CLAIMED", claimed_by=other)
        payload = self.detail(task)
        assert payload["state"] == "CLAIMED" and payload["claimed_by_id"] == str(other.id)
        assert payload["zone_id"] == str(zone.id)
        assert self.client.post(f"/dispatch/requests/{task.id}/complete/", {}, format="json").status_code == 409

    def test_target_projection_batches_fifty_calls_and_deliveries(self):
        table, occupancy = self.visit()
        tasks = []
        for index in range(50):
            tasks.append(DispatchTask.objects.create(
                venue=self.venue, task_type="SERVICE_REQUEST", destination_occupancy=occupancy,
                destination_table=table,
            ))
            tab = Tab.objects.create(venue=self.venue)
            TabOccupancyAssignment.objects.create(tab=tab, occupancy=occupancy)
            tasks.append(ensure_delivery_task_for_ready_order_item(
                item_id=self.ready_item(tab=tab, name=f"Product {index}").id, actor=self.actor,
            ))
        with self.assertNumQueries(3):
            loaded = list(staff_tasks(DispatchTask.objects.filter(id__in=[task.id for task in tasks])))
            targets = StaffTargets(loaded, venue_id=self.venue.id)
            projected = [targets.target(task) for task in loaded]
        assert len(projected) == 100
        assert sum(target["kind"] == "TAB" for target in projected) == 50


@skipUnlessDBFeature("has_select_for_update")
class GuestTargetConcurrencyTests(TransactionTestCase):
    setUp = foundation.DispatchFoundationTests.setUp
    visit = DispatchTargetTests.visit

    def test_same_guest_intent_keeps_one_original_account_snapshot(self):
        table, _ = self.visit()
        guest = resolve_table_qr(public_token=table.public_token)
        tab = create_or_get_guest_tab(session_token=guest.token, display_label="Original")
        request_id = uuid.uuid4()

        def create(_):
            close_old_connections()
            try:
                task = create_service_request(
                    request_id=request_id, task_type="BILL_REQUEST", session_token=guest.token,
                )
                return task.id, task.requested_tab_id, task.requesting_guest_session_id
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(create, range(2)))
        assert results == [(request_id, tab.id, guest.session.id)] * 2
        assert DispatchTask.objects.count() == 1
        assert AuditEvent.objects.filter(event_type="dispatch.service_requested").count() == 1
