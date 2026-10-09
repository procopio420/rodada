from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.access.models import (
    DeviceRegistration,
    StaffMember,
    StaffSession,
    VenueStaffMembership,
)
from modules.audit.models import AuditEvent
from modules.catalog.models import Product
from modules.ledger.models import Charge
from modules.ordering.models import Order, Tab
from modules.venue.models import Venue


class ByodClosureTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="BYOD test", slug="byod-test")
        self.waiter = self.staff("waiter", "STAFF")
        self.owner = self.staff("owner", "OWNER")
        self.product = Product.objects.create(
            venue=self.venue, name="Water", price_cents=500, fulfillment_station="BAR"
        )
        self.tab = Tab.objects.create(venue=self.venue)

    def staff(self, name, role):
        staff = StaffMember.objects.create(display_name=name, login_identifier="byod-" + name)
        staff.set_pin("2468")
        staff.save()
        VenueStaffMembership.objects.create(venue=self.venue, staff_member=staff, role=role)
        return staff

    def login_response(self, staff, installation):
        return APIClient().post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": staff.login_identifier,
                "pin": "2468",
                "installation_id": installation,
                "platform": "ANDROID",
            },
            format="json",
        )

    def login(self, staff, installation):
        response = self.login_response(staff, installation)
        assert response.status_code == 200, response.json()
        return response.json()

    def api_client(self, tokens):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer " + tokens["access_token"])
        return client

    def order(self, tokens, key="order"):
        return self.api_client(tokens).post(
            f"/tabs/{self.tab.pk}/orders/confirm/",
            {
                "idempotency_key": key,
                "lines": [{"product_id": str(self.product.pk), "quantity": 1}],
            },
            format="json",
        )

    def owner_client(self):
        client = self.api_client(self.login(self.owner, "owner-install"))
        assert (
            client.post("/auth/reauthenticate/", {"pin": "2468"}, format="json").status_code == 200
        )
        return client

    def test_first_untrusted_login_orders_and_records_registration_and_domain_provenance(self):
        tokens = self.login(self.waiter, "personal-install")
        assert tokens["device"]["trust_state"] == "UNTRUSTED"
        assert self.api_client(tokens).get("/tabs/").status_code == 200
        assert self.order(tokens).status_code == 201
        assert Order.objects.get().confirmed_by == self.waiter
        assert Charge.objects.get().amount_cents == 500
        for event_type in ("auth.device_registered", "auth.login_succeeded", "order.confirmed"):
            event = AuditEvent.objects.get(event_type=event_type)
            assert event.actor_staff_id == self.waiter.pk
            assert str(event.actor_session_id) == tokens["session_id"]
            assert str(event.device_id) == tokens["device"]["id"]
            assert event.venue_id == self.venue.pk and event.occurred_at
        self.login(self.waiter, "personal-install")
        assert AuditEvent.objects.filter(event_type="auth.device_registered").count() == 1
        assert DeviceRegistration.objects.count() == 1
        text = str(list(AuditEvent.objects.values("metadata")))
        assert "personal-install" not in text and "2468" not in text
        assert tokens["access_token"] not in text and tokens["refresh_token"] not in text

    def test_replacement_phone_operates_while_old_installation_remains_active(self):
        old = self.login(self.waiter, "old-phone")
        new = self.login(self.waiter, "new-phone")
        assert old["device"]["id"] != new["device"]["id"]
        assert self.order(old, "old").status_code == 201
        assert self.order(new, "new").status_code == 201
        assert DeviceRegistration.objects.filter(trust_state="UNTRUSTED").count() == 2

    def test_installation_revoke_is_idempotent_and_reinstall_keeps_membership(self):
        old = self.login(self.waiter, "lost-install")
        new = self.login(self.waiter, "replacement-install")
        owner = self.owner_client()
        path = f"/manage/access/devices/{old['device']['id']}/"
        for _ in range(2):
            assert (
                owner.patch(
                    path, {"trust_state": "REVOKED", "reason": "lost"}, format="json"
                ).status_code
                == 200
            )
        assert AuditEvent.objects.filter(event_type="auth.device_revoked").count() == 1
        assert self.order(old).status_code == 401
        refresh = APIClient().post(
            "/auth/refresh/", {"refresh_token": old["refresh_token"]}, format="json"
        )
        assert refresh.status_code == 401 and refresh.json()["code"] == "SESSION_REVOKED"
        assert self.login_response(self.waiter, "lost-install").json()["code"] == "DEVICE_REVOKED"
        assert self.order(new, "replacement").status_code == 201
        reinstall = self.login(self.waiter, "reinstalled-random-id")
        assert self.order(reinstall, "reinstalled").status_code == 201
        assert VenueStaffMembership.objects.get(staff_member=self.waiter).status == "ACTIVE"

    def test_membership_suspend_and_revoke_deny_every_installation_and_new_login(self):
        for status in ("SUSPENDED", "REVOKED"):
            with self.subTest(status=status):
                membership = VenueStaffMembership.objects.get(staff_member=self.waiter)
                membership.status = "ACTIVE"
                membership.save()
                phones = [self.login(self.waiter, name) for name in ("phone-a", "phone-b")]
                owner = self.owner_client()
                response = owner.patch(
                    f"/manage/access/memberships/{membership.pk}/",
                    {
                        "expected_version": membership.version,
                        "status": status,
                    },
                    format="json",
                )
                assert response.status_code == 200, response.json()
                for tokens in phones:
                    assert self.order(tokens).status_code == 401
                    assert (
                        APIClient()
                        .post(
                            "/auth/refresh/",
                            {"refresh_token": tokens["refresh_token"]},
                            format="json",
                        )
                        .status_code
                        == 401
                    )
                denied = self.login_response(self.waiter, "unknown-" + status)
                assert denied.status_code == 403 and denied.json()["code"] == "MEMBERSHIP_" + status
        assert not Order.objects.exists() and not Charge.objects.exists()

    def test_untrusted_refresh_lock_and_expiry_never_mutate(self):
        tokens = self.login(self.waiter, "personal")
        refresh = APIClient().post(
            "/auth/refresh/", {"refresh_token": tokens["refresh_token"]}, format="json"
        )
        assert refresh.status_code == 200
        rotated = refresh.json()
        assert self.order(rotated).status_code == 201
        assert self.api_client(rotated).post("/auth/lock/", {}, format="json").status_code == 204
        assert self.order(rotated, "locked").status_code == 401
        expired = self.login(self.waiter, "personal")
        StaffSession.objects.filter(pk=expired["session_id"]).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        assert self.order(expired, "expired").json()["code"] == "SESSION_EXPIRED"
        assert Order.objects.count() == 1 and Charge.objects.count() == 1

    def test_version_conflict_returns_current_membership_for_review(self):
        membership = VenueStaffMembership.objects.get(staff_member=self.waiter)
        owner = self.owner_client()
        path = f"/manage/access/memberships/{membership.pk}/"
        assert (
            owner.patch(path, {"expected_version": 1, "role": "CASHIER"}, format="json").status_code
            == 200
        )
        stale = owner.patch(path, {"expected_version": 1, "role": "MANAGER"}, format="json")
        assert stale.status_code == 409
        assert stale.json()["current_membership"] == {
            "id": str(membership.pk),
            "role": "CASHIER",
            "status": "ACTIVE",
            "version": 2,
        }

    def test_replay_keeps_original_session_even_after_new_phone_login(self):
        from modules.access.services import AccessServiceError, authorize_replayed_command

        old = self.login(self.waiter, "original-phone")
        self.api_client(old).post("/auth/lock/", {}, format="json")
        new = self.login(self.waiter, "new-phone")
        assert self.order(new, "new-session").status_code == 201
        with self.assertRaises(AccessServiceError) as denied:
            authorize_replayed_command(
                session_id=old["session_id"], required_capability="order.confirm"
            )
        assert denied.exception.code == "SESSION_REVOKED"
        assert Order.objects.count() == 1

    def test_refund_direct_denial_reauthentication_and_exact_retry(self):
        from modules.ledger.models import Refund

        tokens = self.login(self.owner, "refund-owner")
        client = self.api_client(tokens)
        assert self.order(tokens).status_code == 201
        payment = client.post(
            f"/tabs/{self.tab.pk}/payments/",
            {
                "amount_cents": 500,
                "method": "EXTERNAL_TERMINAL",
                "idempotency_key": "paid",
            },
            format="json",
        )
        assert payment.status_code == 201, payment.json()
        path = f"/payments/{payment.json()['id']}/refunds/"
        body = {"amount_cents": 100, "reason": "Review", "idempotency_key": "same-refund"}
        waiter = self.api_client(self.login(self.waiter, "refund-waiter"))
        denied = waiter.post(path, body, format="json")
        assert denied.status_code == 403 and denied.json()["code"] == "CAPABILITY_REQUIRED"
        stale = client.post(path, body, format="json")
        assert stale.status_code == 403 and stale.json()["code"] == "REAUTH_REQUIRED"
        assert not Refund.objects.exists()
        assert (
            client.post("/auth/reauthenticate/", {"pin": "2468"}, format="json").status_code == 200
        )
        first = client.post(path, body, format="json")
        replay = client.post(path, body, format="json")
        assert first.status_code == 201 and replay.status_code == 200
        assert first.json()["id"] == replay.json()["id"]
        assert Refund.objects.count() == 1

    def test_shared_switch_next_order_has_new_operator_session_and_same_device(self):
        first = self.login(self.waiter, "shared-installation")
        owner = self.owner_client()
        assert (
            owner.patch(
                f"/manage/access/devices/{first['device']['id']}/",
                {"trust_state": "TRUSTED"},
                format="json",
            ).status_code
            == 200
        )
        switched = self.api_client(first).post(
            "/auth/switch-operator/",
            {
                "login_identifier": self.owner.login_identifier,
                "pin": "2468",
            },
            format="json",
        )
        assert switched.status_code == 200
        second = switched.json()
        assert second["device"]["id"] == first["device"]["id"]
        assert self.order(second).status_code == 201
        assert self.order(first, "old-actor").json()["code"] == "SESSION_SUPERSEDED"
        event = AuditEvent.objects.get(event_type="order.confirmed")
        assert event.actor_staff_id == self.owner.pk
        assert str(event.actor_session_id) == second["session_id"]
        assert str(event.device_id) == first["device"]["id"]
        assert Order.objects.get().confirmed_by == self.owner

    def test_real_guest_session_cannot_use_staff_order_endpoint(self):
        from modules.hospitality.models import Table

        table = Table.objects.create(
            venue=self.venue, label="Guest test", guest_ordering_mode="DIRECT"
        )
        guest = APIClient()
        resolved = guest.post("/guest/qr/resolve/", {"token": table.public_token}, format="json")
        assert resolved.status_code == 201
        token = resolved.json()["guest_session_token"]
        guest.credentials(HTTP_X_GUEST_SESSION=token)
        assert guest.get("/guest/catalog/").status_code == 200
        guest.credentials(HTTP_AUTHORIZATION="Bearer " + token)
        denied = guest.post(
            f"/tabs/{self.tab.pk}/orders/confirm/",
            {
                "idempotency_key": "guest-staff",
                "lines": [{"product_id": str(self.product.pk), "quantity": 1}],
            },
            format="json",
        )
        assert denied.status_code == 401 and denied.json()["code"] == "AUTH_REQUIRED"
        assert not Order.objects.exists() and not Charge.objects.exists()


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks")
class MembershipConcurrencyTests(TransactionTestCase):
    def test_parallel_role_updates_only_one_wins_and_conflict_exposes_current_state(self):
        from modules.access.services import AccessServiceError, update_membership_admin

        venue = Venue.objects.create(name="Role race", slug="role-race")
        target = StaffMember.objects.create(display_name="Target", login_identifier="race-target")
        membership = VenueStaffMembership.objects.create(
            venue=venue, staff_member=target, role="STAFF"
        )
        sessions = []
        for index in range(2):
            manager = StaffMember.objects.create(
                display_name="Owner", login_identifier=f"race-owner-{index}"
            )
            member = VenueStaffMembership.objects.create(
                venue=venue, staff_member=manager, role="OWNER"
            )
            sessions.append(
                StaffSession.objects.create(
                    venue=venue,
                    staff_member=manager,
                    membership=member,
                    expires_at=timezone.now() + timedelta(hours=1),
                )
            )
        barrier = Barrier(2)

        def update(index):
            close_old_connections()
            try:
                barrier.wait(10)
                try:
                    changed = update_membership_admin(
                        actor_session=sessions[index],
                        membership_id=membership.pk,
                        expected_version=1,
                        role=("CASHIER", "MANAGER")[index],
                    )
                    return ("PASS", changed.role)
                except AccessServiceError as error:
                    return (error.code, error.details["current_membership"]["role"])
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(update, range(2)))
        assert sorted(result[0] for result in results) == ["PASS", "VERSION_CONFLICT"]
        membership.refresh_from_db()
        assert membership.version == 2 and all(result[1] == membership.role for result in results)
        assert AuditEvent.objects.filter(event_type="membership.role_changed").count() == 1
