"""Spec 004 GUEST-006: opt-in customer identity, scope and takeover barriers."""

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.audit.models import AuditEvent
from modules.guest_access.customer_identity import (
    claim_customer_tab, customer_context, login_customer, logout_customer,
    register_customer,
)
from modules.guest_access.models import CustomerAuthSession, CustomerCredential
from modules.guest_access.services import (
    GuestAccessError, create_or_get_guest_tab, resolve_table_qr,
)
from modules.hospitality.models import GuestOrderingMode, Table, TableOccupancy
from modules.house_account.models import Customer, Relationship
from modules.ordering.models import Order, Tab
from modules.venue.models import Venue
from tests.test_guest_access import GuestAccessServiceTests


class GuestCustomerIdentityTests(TestCase):
    setUp = GuestAccessServiceTests.setUp
    resolve = GuestAccessServiceTests.resolve

    def prepared(self):
        resolution = self.resolve()
        tab = create_or_get_guest_tab(session_token=resolution.token)
        return resolution, tab

    def enroll(self, token, username="ana_01", name="Ana"):
        return register_customer(
            guest_token=token, username=username,
            password="passphrase-strong-2026", display_name=name,
        )

    def test_enroll_does_not_mutate_existing_financial_facts(self):
        resolution, tab = self.prepared()
        order = Order.objects.create(tab=tab, source="GUEST")
        original_version = tab.version
        customer, proof = self.enroll(resolution.token)
        tab.refresh_from_db()
        assert tab.customer_id == customer.id
        assert tab.version == original_version + 1
        assert tab.orders.get().id == order.id
        assert tab.charges.count() == 0
        assert tab.payments.count() == 0
        assert Relationship.objects.get(venue=self.venue, customer=customer).kind == "VISITOR"
        data = customer_context(guest_token=resolution.token, auth_token=proof)
        assert data["authenticated"] is True
        assert data["linked_tab_id"] == str(tab.id)
        assert CustomerAuthSession.objects.get(credential__customer=customer).token_digest != proof
        assert AuditEvent.objects.filter(event_type="guest_customer.registered").count() == 1

    def test_login_and_same_occupancy_claim_without_name_proof(self):
        first, tab = self.prepared()
        customer, proof = self.enroll(first.token)
        second = self.resolve()
        # Proof from another GuestSession is not portable.
        with self.assertRaises(GuestAccessError):
            customer_context(guest_token=second.token, auth_token=proof)
        linked_customer, login_token = login_customer(
            guest_token=second.token, username="ana_01",
            password="passphrase-strong-2026",
        )
        assert linked_customer.id == customer.id
        ctx = customer_context(guest_token=second.token, auth_token=login_token)
        assert [t["id"] for t in ctx["claimable_tabs"]] == [str(tab.id)]
        claimed = claim_customer_tab(
            guest_token=second.token, auth_token=login_token, target_tab_id=tab.id,
        )
        assert claimed.id == tab.id
        second.session.refresh_from_db()
        assert second.session.tab_id == tab.id
        assert tab.customer_id is None or Customer.objects.filter(pk=customer.pk).exists()
        again = claim_customer_tab(
            guest_token=second.token, auth_token=login_token, target_tab_id=tab.id,
        )
        assert again.id == tab.id
        assert AuditEvent.objects.filter(event_type="guest_customer.tab_claimed").count() == 1

    def test_cross_venue_stolen_auth_cannot_claim_or_discover_tabs(self):
        first, tab = self.prepared()
        customer, auth = self.enroll(first.token)
        other = Venue.objects.create(name="Outra Casa", slug="identity-other-venue")
        other_table = Table.objects.create(
            venue=other, label="27",
            guest_ordering_mode=GuestOrderingMode.DIRECT,
        )
        guest_other = resolve_table_qr(public_token=other_table.public_token)
        with self.assertRaises(GuestAccessError) as mismatch:
            customer_context(guest_token=guest_other.token, auth_token=auth)
        assert mismatch.exception.code == "CUSTOMER_AUTH_REVOKED"
        with self.assertRaises(GuestAccessError) as foreign_login:
            login_customer(
                guest_token=guest_other.token, username="ana_01",
                password="passphrase-strong-2026",
            )
        assert foreign_login.exception.code == "CUSTOMER_NOT_IN_VENUE"
        assert tab.customer_id is None or Customer.objects.filter(pk=customer.pk).exists()

    def test_another_authenticated_profile_cannot_take_an_existing_tab(self):
        first, tab = self.prepared()
        owner, _ = self.enroll(first.token)
        second = self.resolve()
        foreign_tab = create_or_get_guest_tab(session_token=second.token)
        _other, other_auth = self.enroll(second.token, username="outro_01", name="Outra")
        with self.assertRaises(GuestAccessError) as wrong:
            claim_customer_tab(
                guest_token=second.token, auth_token=other_auth, target_tab_id=tab.id,
            )
        assert wrong.exception.code == "GUEST_TAB_ALREADY_LINKED"
        assert foreign_tab.customer_id is None or foreign_tab.customer_id != owner.id

    def test_legacy_customer_name_cannot_be_enrolled_or_claimed(self):
        resolution, tab = self.prepared()
        legacy = Customer.objects.create(display_name="Ana")
        Relationship.objects.create(venue=self.venue, customer=legacy)
        tab.customer = legacy
        tab.save(update_fields=["customer"])
        with self.assertRaises(GuestAccessError) as error:
            self.enroll(resolution.token, username="ana-name-only")
        assert error.exception.code == "TAB_CANNOT_ENROLL"
        assert not CustomerCredential.objects.exists()

    def test_login_rate_lockout_and_revocation(self):
        first, tab = self.prepared()
        customer, original = self.enroll(first.token)
        for _ in range(5):
            user, credential = login_customer(
                guest_token=first.token, username="ana_01", password="wrong",
            )
            assert user is None and credential == ""
        row = CustomerCredential.objects.get(customer=customer)
        assert row.locked_until is not None and row.locked_until > timezone.now()
        user, credential = login_customer(
            guest_token=first.token, username="ana_01",
            password="passphrase-strong-2026",
        )
        assert user is None and credential == ""
        logout_customer(guest_token=first.token, auth_token=original)
        with self.assertRaises(GuestAccessError) as revoked:
            customer_context(guest_token=first.token, auth_token=original)
        assert revoked.exception.code == "CUSTOMER_AUTH_REVOKED"
        assert tab.customer_id is None or Customer.objects.filter(pk=customer.pk).exists()

    def test_guest_release_revokes_profile_continuity(self):
        first, tab = self.prepared()
        _, auth = self.enroll(first.token)
        occupancy = TableOccupancy.objects.get(table=self.table)
        occupancy.released_at = timezone.now()
        occupancy.save(update_fields=["released_at"])
        with self.assertRaises(GuestAccessError) as revoked:
            customer_context(guest_token=first.token, auth_token=auth)
        assert revoked.exception.code == "GUEST_SESSION_REVOKED"
        assert tab.customer_id is not None

    def test_http_contract_does_not_accept_label_or_table_number(self):
        resolution, tab = self.prepared()
        client = APIClient()
        bad = client.post("/guest/customer/claim/", {
            "target_tab_id": str(tab.id), "display_name": "Ana",
        }, format="json", HTTP_X_GUEST_SESSION=resolution.token)
        assert bad.status_code == 401
        enrolled = client.post("/guest/customer/register/", {
            "username": "ana_01", "password": "passphrase-strong-2026",
            "display_name": "Ana",
        }, format="json", HTTP_X_GUEST_SESSION=resolution.token)
        assert enrolled.status_code == 201, enrolled.json()
        proof = enrolled.json()["customer_auth_token"]
        claim = client.post("/guest/customer/claim/", {
            "target_tab_id": str(tab.id),
        }, format="json", HTTP_X_GUEST_SESSION=resolution.token,
            HTTP_X_CUSTOMER_SESSION=proof)
        assert claim.status_code == 200, claim.json()
        logout = client.post("/guest/customer/logout/", {}, format="json",
            HTTP_X_GUEST_SESSION=resolution.token, HTTP_X_CUSTOMER_SESSION=proof)
        assert logout.status_code == 200
