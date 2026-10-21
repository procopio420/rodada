"""Spec031/033: canonical policy, one ledger, original idempotent intent."""

from django.test import TestCase
from rest_framework.test import APIClient

from modules.audit.models import AuditEvent
from modules.ledger.models import Charge, Payment
from modules.ordering.models import Order, Tab
from tests.test_house_account import HouseFixture
from tests.test_pricing import PricingFixture
from tests.test_tab_operations import OperationFixture


class SpendingLimitModesTests(HouseFixture, TestCase):
    path = "/house-account/enforcement/"

    def mode(self, mode, key="policy", version=1):
        self.reauth()
        response = self.manager.put(
            self.path,
            {
                "mode": mode,
                "expected_version": version,
                "reason": "Synthetic policy test",
                "idempotency_key": key,
            },
            format="json",
        )
        assert response.status_code == 200, response.json()
        return response.json()

    def test_default_warn_and_replay_after_mode_change_share_one_ledger(self):
        assert self.staff.get(self.path).json()["mode"] == "ENFORCE"
        tab = self.tab()
        self.order(tab, quantity=2)
        self.order(
            tab,
            quantity=2,
            key="blocked",
            status=409,
            extra={"spending_limit_mode": "WARN_ONLY", "mode": "WARN_ONLY"},
        )
        self.mode("WARN_ONLY")
        order = self.order(tab, quantity=2, key="warn")
        assert self.order(tab, quantity=2, key="warn", status=200)["id"] == order["id"]
        detail = self.detail(tab)
        assert detail["exposure_cents"] == 4000
        assert detail["spending_limit_mode"] == "WARN_ONLY"
        assert detail["spending_limit_policy_version"] == 2
        assert detail["limit_exceeded"] and detail["limit_warning"]
        assert not detail["consumption_blocked"] and detail["state"] == "OPEN"
        assert Order.objects.count() == Charge.objects.count() == 2
        assert Payment.objects.count() == 0
        assert AuditEvent.objects.filter(event_type="spending_limit.exceeded").count() == 1
        self.mode("ENFORCE", key="back", version=2)
        assert self.order(tab, quantity=2, key="warn", status=200)["id"] == order["id"]
        assert (
            self.order(tab, quantity=1, key="new", status=409)["code"] == "SPENDING_LIMIT_EXCEEDED"
        )
        self.order(tab, quantity=1, key="warn", status=409)
        assert self.detail(tab)["exposure_cents"] == 4000

    def test_cas_original_replay_and_noop(self):
        first = self.mode("WARN_ONLY")
        self.mode("ENFORCE", key="back", version=2)
        assert self.mode("WARN_ONLY") == first
        assert self.mode("ENFORCE", key="noop", version=3)["version"] == 3
        for mode, key, code in [
            ("ENFORCE", "policy", "IDEMPOTENCY_CONFLICT"),
            ("WARN_ONLY", "stale", "POLICY_VERSION_CONFLICT"),
        ]:
            response = self.manager.put(
                self.path,
                {
                    "mode": mode,
                    "expected_version": 1,
                    "reason": "Synthetic policy test",
                    "idempotency_key": key,
                },
                format="json",
            )
            assert response.status_code == 409 and response.json()["code"] == code
        assert AuditEvent.objects.filter(event_type="spending_limit_policy.updated").count() == 2

    def test_write_requires_manager_capability_and_recent_pin(self):
        body = {
            "mode": "WARN_ONLY",
            "expected_version": 1,
            "reason": "Test",
            "idempotency_key": "denied",
        }
        for client in (self.staff, self.cashier, self.manager, APIClient()):
            assert client.put(self.path, body, format="json").status_code in (401, 403)
        self.reauth()
        assert (
            self.manager.put(self.path, {**body, "mode": "INVALID"}, format="json").status_code
            == 400
        )
        assert self.staff.get(self.path).json()["mode"] == "ENFORCE"

    def test_zero_limit_and_independent_attention(self):
        tab = self.tab()
        Tab.objects.filter(pk=tab).update(operating_limit_cents=0)
        self.order(tab, status=409)
        self.mode("WARN_ONLY")
        self.order(tab)
        detail = self.detail(tab)
        assert detail["percentage_used"] is None
        assert detail["limit_exceeded"] and detail["limit_warning"]
        assert not detail["consumption_blocked"] and detail["state"] == "OPEN"
        Tab.objects.filter(pk=tab).update(state="REQUIRES_ACTION", action_reasons=["MANUAL_REVIEW"])
        assert self.order(tab, key="review", status=409)["code"] == "TAB_REQUIRES_ACTION"
        assert self.detail(tab)["action_reasons"] == ["MANUAL_REVIEW"]
        assert Order.objects.count() == 1

    def test_warn_never_overrides_availability_closed_or_tenant(self):
        from modules.catalog.models import ProductAvailability
        from modules.house_account.models import VenueSpendingLimitPolicy
        from modules.venue.models import Venue

        self.mode("WARN_ONLY")
        tab = self.tab()
        ProductAvailability.objects.filter(product=self.product).update(state="UNAVAILABLE")
        assert self.order(tab, status=409)["code"] == "PRODUCTS_NOT_CONFIRMABLE"
        ProductAvailability.objects.filter(product=self.product).update(state="AVAILABLE")
        Tab.objects.filter(pk=tab).update(state="CLOSED")
        assert self.order(tab, status=409)["code"] == "TAB_NOT_OPEN"
        foreign = Venue.objects.create(name="Foreign", slug="foreign-policy")
        foreign_tab = Tab.objects.create(venue=foreign)
        assert self.order(str(foreign_tab.id), status=404)["code"] == "TAB_NOT_FOUND"
        assert Order.objects.count() == 0
        assert VenueSpendingLimitPolicy.objects.get(venue=foreign).mode == "ENFORCE"
        assert self.staff.get(self.path).json()["mode"] == "WARN_ONLY"


class SpendingTransfersTests(OperationFixture, TestCase):
    mode = SpendingLimitModesTests.mode
    path = SpendingLimitModesTests.path

    def test_transfer_and_replay_obey_same_policy(self):
        source, destination = self.tab(), self.tab()
        self.order(source, quantity=2)
        self.order(destination, quantity=2)
        command = self.command(source, destination, lines=[self.line(source, quantity=2)])
        assert self.commit(source, command, status=409)["code"] == "SPENDING_LIMIT_EXCEEDED"
        self.mode("WARN_ONLY")
        result = self.commit(source, command)
        assert self.detail(destination)["exposure_cents"] == 4000
        assert self.detail(source)["exposure_cents"] == 0
        self.mode("ENFORCE", key="back", version=2)
        assert self.commit(source, command) == result
        assert AuditEvent.objects.filter(event_type="spending_limit.exceeded").count() == 1
        assert Charge.objects.count() == 2


class SpendingPricingTests(PricingFixture, TestCase):
    def test_positive_service_charge_and_replay_obey_same_policy(self):
        self.tab.operating_limit_cents = 2000
        self.tab.save(update_fields=["operating_limit_cents"])
        command = self.command(kind="SERVICE_CHARGE", value=1000)
        denied = self.apply(command)
        assert denied.status_code == 409 and denied.json()["code"] == "SPENDING_LIMIT_EXCEEDED"
        path = "/house-account/enforcement/"
        body = {
            "mode": "WARN_ONLY",
            "expected_version": 1,
            "reason": "Test",
            "idempotency_key": "warn",
        }
        assert self.client.put(path, body, format="json").status_code == 200
        result = self.apply(command)
        assert result.status_code == 200, result.json()
        result = result.json()
        assert self.client.get(f"/tabs/{self.tab.id}/").json()["exposure_cents"] == 2200
        assert (
            self.client.put(
                path,
                {**body, "mode": "ENFORCE", "expected_version": 2, "idempotency_key": "back"},
                format="json",
            ).status_code
            == 200
        )
        assert self.apply(command).json()["effect_cents"] == result["effect_cents"]
        assert AuditEvent.objects.filter(event_type="spending_limit.exceeded").count() == 1


class SpendingBoundaryTests(HouseFixture, TestCase):
    mode = SpendingLimitModesTests.mode
    path = SpendingLimitModesTests.path

    def test_boundaries_use_canonical_price_and_partial_payment(self):
        self.mode("WARN_ONLY")
        for percent in (0, 79, 80, 99, 100, 120):
            self.product.price_cents = percent * 100
            self.product.save(update_fields=["price_cents"])
            tab = self.tab()
            Tab.objects.filter(pk=tab).update(operating_limit_cents=10000)
            self.order(tab)
            detail = self.detail(tab)
            assert detail["percentage_used"] == percent
            assert detail["limit_warning"] == (percent >= 80)
            assert detail["limit_exceeded"] == (percent > 100)
            assert not detail["consumption_blocked"] and detail["state"] == "OPEN"
            assert detail["remaining_capacity_cents"] == max(0, 10000 - percent * 100)
        self.payment(tab, amount=5000)
        detail = self.detail(tab)
        assert detail["exposure_cents"] == 7000 and detail["state"] == "OPEN"
        assert detail["remaining_capacity_cents"] == 3000
        assert not detail["limit_warning"]

    def test_missing_policy_read_falls_back_without_creating_or_relaxing(self):
        from modules.house_account.models import VenueSpendingLimitPolicy

        VenueSpendingLimitPolicy.objects.filter(venue=self.venue).delete()
        tab = self.tab()
        assert not VenueSpendingLimitPolicy.objects.filter(venue=self.venue).exists()
        current = self.staff.get(self.path).json()
        assert current["mode"] == "ENFORCE" and current["version"] is None and current["fallback"]
        assert self.order(tab, quantity=4, status=409)["code"] == "SPENDING_LIMIT_EXCEEDED"
        self.reauth()
        denied = self.manager.put(
            self.path,
            {
                "mode": "WARN_ONLY",
                "expected_version": 1,
                "idempotency_key": "missing",
                "reason": "Test",
            },
            format="json",
        )
        assert denied.status_code == 409 and denied.json()["code"] == "POLICY_MISSING"


class SpendingPolicySecurityTests(HouseFixture, TestCase):
    path = SpendingLimitModesTests.path
    mode = SpendingLimitModesTests.mode

    def test_non_manager_with_capability_and_pin_cannot_change_policy(self):
        from modules.access.models import VenueStaffMembership

        VenueStaffMembership.objects.filter(
            venue=self.venue, staff_member__login_identifier="house-staff"
        ).update(capability_overrides={"allow": ["venue.configure"]})
        self.post(self.staff, "/auth/reauthenticate/", {"pin": "0420"})
        response = self.staff.put(
            self.path,
            {
                "mode": "WARN_ONLY",
                "expected_version": 1,
                "reason": "Test",
                "idempotency_key": "role-denied",
            },
            format="json",
        )
        assert response.status_code == 403 and response.json()["code"] == "MANAGER_REQUIRED"
        assert self.staff.get(self.path).json()["mode"] == "ENFORCE"

    def test_revoked_manager_cannot_read_or_replay_policy_write(self):
        from django.utils import timezone

        from modules.access.models import StaffSession

        self.mode("WARN_ONLY")
        StaffSession.objects.filter(staff_member__login_identifier="house-manager").update(
            revoked_at=timezone.now()
        )
        assert self.manager.get(self.path).status_code in (401, 403)
        response = self.manager.put(
            self.path,
            {
                "mode": "WARN_ONLY",
                "expected_version": 1,
                "reason": "Synthetic policy test",
                "idempotency_key": "policy",
            },
            format="json",
        )
        assert response.status_code in (401, 403)
        assert AuditEvent.objects.filter(event_type="spending_limit_policy.updated").count() == 1

    def test_query_and_body_cannot_select_foreign_policy(self):
        from modules.venue.models import Venue

        original = self.venue
        foreign = Venue.objects.create(name="Other policy", slug="other-policy")
        self.venue = foreign
        other = self.login("foreign-manager", "MANAGER")
        self.venue = original
        self.reauth()
        result = self.manager.put(
            self.path,
            {
                "mode": "WARN_ONLY",
                "expected_version": 1,
                "reason": "Own policy",
                "idempotency_key": "own",
                "venue_id": str(foreign.id),
            },
            format="json",
        )
        assert result.status_code == 200
        assert (
            self.staff.get(self.path, {"venue_id": str(foreign.id)}).json()["mode"] == "WARN_ONLY"
        )
        assert other.get(self.path, {"venue_id": str(original.id)}).json()["mode"] == "ENFORCE"
        assert (
            other.put(
                self.path,
                {
                    "mode": "WARN_ONLY",
                    "expected_version": 1,
                    "reason": "Own policy",
                    "idempotency_key": "own",
                },
                format="json",
            ).status_code
            == 403
        )

    def test_editor_context_is_bound_at_server_before_receipt_or_write(self):
        import uuid

        from modules.access.models import StaffSession
        from modules.house_account.models import SpendingLimitPolicyCommand

        self.reauth()
        session = StaffSession.objects.get(staff_member__login_identifier="house-manager")
        body = {
            "mode": "WARN_ONLY",
            "expected_version": 1,
            "reason": "Bound editor",
            "idempotency_key": "bound",
            "expected_venue_id": str(self.venue.id),
            "expected_session_id": str(session.id),
        }
        for field in ("expected_venue_id", "expected_session_id"):
            response = self.manager.put(
                self.path, {**body, field: str(uuid.uuid4())}, format="json"
            )
            assert (
                response.status_code == 409 and response.json()["code"] == "ACTOR_CONTEXT_CHANGED"
            )
        partial = dict(body)
        partial.pop("expected_session_id")
        assert self.manager.put(self.path, partial, format="json").status_code == 409
        assert SpendingLimitPolicyCommand.objects.count() == 0
        assert self.staff.get(self.path).json()["mode"] == "ENFORCE"
        assert self.manager.put(self.path, body, format="json").status_code == 200
        assert (
            self.manager.put(
                self.path, {**body, "expected_session_id": str(uuid.uuid4())}, format="json"
            ).status_code
            == 409
        )
        assert SpendingLimitPolicyCommand.objects.count() == 1
