"""Spec 004 negative authorization, replay and independent-ledger evidence."""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.guest_access.models import GuestSession
from modules.guest_access.services import (
    GuestAccessError,
    confirm_guest_order,
    create_or_get_guest_tab,
    guest_session_context,
    resolve_table_qr,
)
from modules.guest_access.views import _rate_events, _rate_lock
from tests import test_guest_access as fixtures


class Spec004CloseoutTests(TestCase):
    setUp = fixtures.GuestAccessServiceTests.setUp
    resolve = fixtures.GuestAccessServiceTests.resolve
    def test_two_guest_tabs_share_occupancy_but_never_orders_charges_or_payments(self):
        first = self.resolve()
        a = create_or_get_guest_tab(session_token=first.token)
        second = self.resolve()
        b = create_or_get_guest_tab(session_token=second.token)
        assert a.pk != b.pk
        assert a.occupancy_assignments.get().occupancy_id == b.occupancy_assignments.get().occupancy_id
        for token, quantity, tab in [(first.token, 1, a), (second.token, 2, b)]:
            order = confirm_guest_order(session_token=token, lines=[{"product_id": self.product.id, "quantity": quantity}], idempotency_key="same-key-per-tab")
            replay = confirm_guest_order(session_token=token, lines=[{"product_id": self.product.id, "quantity": quantity}], idempotency_key="same-key-per-tab")
            assert replay.pk == order.pk
            context = guest_session_context(session_token=token)
            assert context.tab_id == tab.pk
            assert tab.orders.count() == tab.charges.count() == 1
            assert tab.charges.get().amount_cents == quantity * self.product.price_cents
            assert tab.payments.count() == 0
        assert not a.orders.filter(pk=b.orders.get().pk).exists()

    def assert_terminal_session(self, terminal):
        resolution = self.resolve()
        tab = create_or_get_guest_tab(session_token=resolution.token)
        if terminal == "expired":
            GuestSession.objects.filter(pk=resolution.session.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        else:
            GuestSession.objects.filter(pk=resolution.session.pk).update(revoked_at=timezone.now())
        for command in [lambda: guest_session_context(session_token=resolution.token), lambda: create_or_get_guest_tab(session_token=resolution.token), lambda: confirm_guest_order(session_token=resolution.token, lines=[{"product_id": self.product.id, "quantity": 1}], idempotency_key="terminal")]:
            with self.assertRaises(GuestAccessError) as error:
                command()
            assert error.exception.code == "GUEST_SESSION_EXPIRED"
        assert tab.orders.count() == tab.charges.count() == tab.payments.count() == 0

    def test_raw_id_is_not_a_qr_and_rotated_token_is_rejected(self):
        for token in [str(self.table.pk), "24"]:
            with self.assertRaises(GuestAccessError) as error:
                resolve_table_qr(public_token=token)
            assert error.exception.code == "QR_NOT_FOUND"
        previous = self.table.public_token
        self.table.public_token = "rotated-test-token-for-explicit-revocation"
        self.table.save(update_fields=["public_token"])
        with self.assertRaises(GuestAccessError) as error:
            resolve_table_qr(public_token=previous)
        assert error.exception.code == "QR_NOT_FOUND"

    def test_rate_limit_resolution_and_mutation_reject_without_new_effects(self):
        client = APIClient()
        with _rate_lock:
            _rate_events.clear()
        try:
            for _ in range(30):
                assert client.post("/guest/qr/resolve/", {"token": "missing"}, format="json", REMOTE_ADDR="192.0.2.4").status_code == 404
            assert client.post("/guest/qr/resolve/", {"token": self.table.public_token}, format="json", REMOTE_ADDR="192.0.2.4").status_code == 429
            for _ in range(60):
                assert client.post("/guest/tabs/", {}, format="json", REMOTE_ADDR="192.0.2.5").status_code == 401
            assert client.post("/guest/tabs/", {}, format="json", REMOTE_ADDR="192.0.2.5").status_code == 429
            assert GuestSession.objects.count() == 0
        finally:
            with _rate_lock:
                _rate_events.clear()

    def test_expired_session_denies_all_operations(self):
        self.assert_terminal_session("expired")

    def test_revoked_session_denies_all_operations(self):
        self.assert_terminal_session("revoked")
