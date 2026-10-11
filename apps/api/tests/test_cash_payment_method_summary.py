"""Cashier-facing, tenant-scoped day summary regression tests.

The drawer position intentionally remains separate from venue-wide receipts.
"""
from datetime import date, timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.ledger.models import Payment, PaymentMethod, PaymentStatus, Refund, RefundStatus
from modules.ordering.models import Tab
from modules.venue.calendar import business_boundary, business_date
from modules.venue.models import Venue


class CashPaymentMethodSummaryTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(
            name="Cash summary", slug="cash-summary", timezone="America/Sao_Paulo",
            business_day_cutoff_hour=4,
        )
        self.staff = StaffMember.objects.create(
            display_name="Cashier", login_identifier="cash-summary-cashier"
        )
        self.staff.set_pin("1234")
        self.staff.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(
            venue=self.venue, staff_member=self.staff, role=StaffRole.CASHIER
        )
        self.client = APIClient()
        response = self.client.post("/auth/login/", {
            "venue_slug": self.venue.slug, "login_identifier": self.staff.login_identifier,
            "pin": "1234", "installation_id": "cash-summary-test", "platform": "WEB",
        }, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        self.token = response.json()["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.day = date(2026, 10, 10)
        self.lower = business_boundary(self.venue, self.day)
        self.upper = business_boundary(self.venue, self.day + timedelta(days=1))
        self.tab = Tab.objects.create(venue=self.venue, opened_by=self.staff)
        self._key = 0

    def payment(self, *, tab=None, method=PaymentMethod.CASH, amount=1000,
                when=None, status=PaymentStatus.CONFIRMED):
        self._key += 1
        return Payment.objects.create(
            tab=tab or self.tab, received_by=self.staff,
            method=method, amount_cents=amount,
            idempotency_key=f"cash-summary-{self._key}",
            status=status,
            confirmed_at=when if status in PaymentStatus.confirmed_money_values() else None,
        )

    def refund(self, payment, amount, when, *, status=RefundStatus.CONFIRMED):
        self._key += 1
        return Refund.objects.create(
            payment=payment, amount_cents=amount, status=status,
            confirmed_at=when if status == RefundStatus.CONFIRMED else None,
            created_by=self.staff, idempotency_key=f"cash-summary-refund-{self._key}",
        )

    def summary(self, day=None):
        d = day or self.day
        return self.client.get(f"/cash/received-by-method/?business_date={d.isoformat()}")

    def test_all_methods_net_refunds_and_business_day_boundaries(self):
        now = self.lower + timedelta(hours=2)
        cash = self.payment(method=PaymentMethod.CASH, amount=10000, when=now)
        self.payment(method=PaymentMethod.CARD, amount=6000, when=now)
        self.payment(method=PaymentMethod.PIX, amount=9999, status=PaymentStatus.PENDING)
        self.payment(amount=111, when=self.lower - timedelta(seconds=1))
        self.payment(amount=222, when=self.upper)
        self.refund(cash, 2500, now)
        self.refund(cash, 1234, now, status=RefundStatus.PENDING)

        other = Venue.objects.create(name="Other cash", slug="other-cash")
        other_tab = Tab.objects.create(venue=other, opened_by=self.staff)
        self.payment(tab=other_tab, amount=44444, when=now)

        response = self.summary()
        self.assertEqual(response.status_code, 200, response.content)
        payload = response.json()
        self.assertEqual(payload["scope"], "VENUE_BUSINESS_DATE")
        self.assertEqual(payload["business_date"], "2026-10-10")
        self.assertEqual(payload["paid_cents"], 16000)
        self.assertEqual(payload["refunds_cents"], 2500)
        self.assertEqual(payload["net_received_cents"], 13500)
        self.assertEqual(payload["methods"], [
            {"method": "CARD", "paid_cents": 6000, "refunds_cents": 0,
             "net_received_cents": 6000, "payment_count": 1, "refund_count": 0},
            {"method": "CASH", "paid_cents": 10000, "refunds_cents": 2500,
             "net_received_cents": 7500, "payment_count": 1, "refund_count": 1},
        ])

    def test_refunds_can_make_day_negative_without_rewriting_original_payment(self):
        old_payment = self.payment(
            method=PaymentMethod.PIX, amount=2000, when=self.lower - timedelta(hours=1)
        )
        self.refund(old_payment, 500, self.lower + timedelta(hours=2))
        response = self.summary()
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertEqual(data["paid_cents"], 0)
        self.assertEqual(data["refunds_cents"], 500)
        self.assertEqual(data["net_received_cents"], -500)
        self.assertEqual(data["methods"][0]["method"], "PIX")
        self.assertEqual(data["methods"][0]["refund_count"], 1)
        self.assertEqual(data["methods"][0]["payment_count"], 0)

    def test_authorization_input_validation_and_default_operational_date(self):
        invalid = self.client.get("/cash/received-by-method/?business_date=bad-day")
        self.assertEqual(invalid.status_code, 400)
        self.client.credentials()
        denied = self.summary()
        self.assertIn(denied.status_code, (401, 403))
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        current = self.client.get("/cash/received-by-method/")
        self.assertEqual(current.status_code, 200, current.content)
        self.assertEqual(current.json()["business_date"], business_date(self.venue).isoformat())
        self.assertEqual(current.json()["methods"], [])
