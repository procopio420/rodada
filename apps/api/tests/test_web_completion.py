from datetime import datetime, timedelta, timezone as dt_timezone
from django.test import TestCase
from django.utils import timezone
from modules.audit.models import AuditEvent
from modules.catalog.models import Product, ProductIcon
from modules.cash.models import CashShift
from modules.ledger.models import Payment, Refund, LedgerAdjustment
from modules.ordering.models import OrderItem
from modules.access.context import ActorContext
from modules.access.models import StaffSession
from modules.catalog.services import resolve_or_create_product
from django.test import TransactionTestCase
from django.db import connection, close_old_connections, connections
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from modules.venue.models import Venue
from modules.venue.calendar import business_date, business_boundary
from tests.test_house_account import HouseFixture


class WebCompletionTests(HouseFixture, TestCase):
    def test_catalog_create_reuse_validation_and_authorization(self):
        body = {"name": "  Omelete   especial  ", "price_cents": 1800, "fulfillment_station": "KITCHEN"}
        self.post(self.staff, "/catalog/products/resolve/", body, status=403)
        created = self.post(self.manager, "/catalog/products/resolve/", body, status=201)
        replay = self.post(self.manager, "/catalog/products/resolve/", {**body, "name": "OMELETE especial", "price_cents": 9999}, status=200)
        assert replay["product"]["id"] == created["product"]["id"]
        assert replay["product"]["price_cents"] == 1800
        assert Product.objects.filter(normalized_name="omelete especial").count() == 1
        assert ProductIcon.objects.get(product_id=created["product"]["id"]).generations.filter(status="PENDING").count() == 1
        assert AuditEvent.objects.filter(event_type="catalog.product_created").count() == 1
        for invalid in [{"price_cents": -1}, {"price_cents": 1.5}, {"name": " "}, {"fulfillment_station": "OTHER"}, {"name": "ß" * 160}]:
            self.post(self.manager, "/catalog/products/resolve/", {**body, **invalid}, status=400)
        found = self.manager.get("/catalog/products/?q=omelete").json()["results"]
        assert len(found) == 1 and found[0]["icon"]["status"] == "GENERATING"
        other = Venue.objects.create(name="Other", slug="other-web-completion")
        Product.objects.create(venue=other, name="Omelete outro", price_cents=100, fulfillment_station="BAR")
        assert len(self.manager.get("/catalog/products/?q=omelete").json()["results"]) == 1
        product = Product.objects.get(pk=created["product"]["id"])
        product.active = False; product.save()
        assert not self.manager.get("/catalog/products/?q=omelete").json()["results"]
        assert len(self.manager.get("/catalog/products/?q=omelete&include_inactive=true").json()["results"]) == 1
        replay = self.post(self.manager, "/catalog/products/resolve/", body, status=200)
        assert not replay["product"]["active"]

    def test_report_totals_confirmed_money_and_historical_names(self):
        tab = self.post(self.staff, "/tabs/", {}, status=201)
        self.order(tab["id"], quantity=2, key="report-order")
        self.payment(tab["id"], amount=1000)
        Payment.objects.create(tab_id=tab["id"], amount_cents=9000, method="CARD", status="PENDING", idempotency_key="pending-report", received_by=self.venue.staff_memberships.get(staff_member__login_identifier="house-cashier").staff_member)
        payment = Payment.objects.get(idempotency_key="payment")
        Refund.objects.create(payment=payment, amount_cents=200, idempotency_key="report-refund", confirmed_at=timezone.now(), created_by=payment.received_by)
        item = OrderItem.objects.get(order__tab_id=tab["id"])
        LedgerAdjustment.objects.create(tab_id=tab["id"], order_item=item, kind="ORDER_ITEM_CANCELLATION", amount_cents=-500, idempotency_key="report-adjust", reason_code="test", created_by=payment.received_by)
        self.product.name = "Renamed"; self.product.save()
        today = business_date(self.venue)
        response = self.manager.get(f"/management/reports/?start={today}&end={today}")
        assert response.status_code == 200, response.json()
        report = response.json()
        assert report["totals"]["gross_cents"] == 2000
        assert report["totals"]["net_sales_cents"] == 1500
        assert report["totals"]["paid_cents"] == 1000
        assert report["totals"]["refunds_cents"] == 200
        assert report["totals"]["net_received_cents"] == 800
        assert report["totals"]["current_open_exposure_cents"] == 700
        credit_tab = self.tab()
        self.order(credit_tab, key="credit-order")
        credit_item = OrderItem.objects.get(order__tab_id=credit_tab)
        Payment.objects.create(tab_id=credit_tab, amount_cents=1000, method="CASH", status="CONFIRMED", confirmed_at=timezone.now(), idempotency_key="credit-payment", received_by=payment.received_by)
        LedgerAdjustment.objects.create(tab_id=credit_tab, order_item=credit_item, kind="ORDER_ITEM_CANCELLATION", amount_cents=-500, idempotency_key="credit-report", reason_code="test", created_by=payment.received_by)
        assert self.manager.get(f"/management/reports/?start={today}&end={today}").json()["totals"]["current_open_exposure_cents"] == 700
        assert report["products"][0]["order_item__product_name_snapshot"] == "Água"
        assert report["products"][0]["quantity"] == 2
        assert report["payment_methods"] == [{"method": "EXTERNAL_TERMINAL", "amount_cents": 1000, "count": 1}]
        assert self.staff.get(f"/management/reports/?start={today}&end={today}").status_code == 403
        assert self.manager.get("/management/reports/?start=2026-01-01&end=2025-01-01").status_code == 400
        assert self.manager.get("/management/reports/?start=2020-01-01&end=2026-01-01").status_code == 400

    def test_calendar_cutoff_timezone_and_audit(self):
        response = self.manager.patch("/management/calendar/", {"timezone": "America/Sao_Paulo", "cutoff_hour": 4}, format="json")
        assert response.status_code == 200
        self.venue.refresh_from_db()
        before = datetime(2026, 10, 9, 6, 59, tzinfo=dt_timezone.utc)
        after = before + timedelta(minutes=1)
        assert str(business_date(self.venue, before)) == "2026-10-08"
        assert str(business_date(self.venue, after)) == "2026-10-09"
        assert business_boundary(self.venue, business_date(self.venue, after)).hour == 4
        assert AuditEvent.objects.filter(event_type="business_date_policy.changed").count() == 1
        assert self.manager.patch("/management/calendar/", {"timezone": "Invalid", "cutoff_hour": 4}, format="json").status_code == 400
        assert self.manager.patch("/management/calendar/", {"timezone": "UTC", "cutoff_hour": 24}, format="json").status_code == 400
        assert self.staff.patch("/management/calendar/", {"timezone": "UTC", "cutoff_hour": 4}, format="json").status_code == 403

    def test_history_keeps_old_pending_and_current_shift(self):
        point = self.post(self.manager, "/cash/points/create/", {"label": "History"}, status=201)
        old = self.post(self.manager, "/cash/shifts/", {"cash_point_id": point["id"], "opening_float_cents": 1000, "idempotency_key": "old"}, status=201)
        self.post(self.manager, f'/cash/shifts/{old["id"]}/count/start/', {})
        self.post(self.manager, f'/cash/shifts/{old["id"]}/close/', {"counted_amount_cents": 900})
        current = self.post(self.manager, "/cash/shifts/", {"cash_point_id": point["id"], "opening_float_cents": 1000, "idempotency_key": "current"}, status=201)
        response = self.manager.get(f'/cash/shifts/history/?cash_point_id={point["id"]}')
        assert response.status_code == 200
        rows = response.json()["results"]
        assert {r["id"] for r in rows} == {old["id"], current["id"]}
        assert next(r for r in rows if r["id"] == old["id"])["review_status"] == "PENDING"
        assert CashShift.objects.get(pk=current["id"]).status == "OPEN"
        assert self.manager.get(f'/cash/shifts/history/?cash_point_id={point["id"]}&offset=2').json()["results"] == []

    def test_report_cutoff_and_payment_confirmation_dates(self):
        self.venue.business_day_cutoff_hour = 4; self.venue.save()
        tab = self.tab(); self.order(tab)
        from modules.ledger.models import Charge
        at = datetime(2026, 10, 9, 6, 59, tzinfo=dt_timezone.utc)
        Charge.objects.filter(tab_id=tab).update(created_at=at)
        self.payment(tab)
        Payment.objects.filter(tab_id=tab).update(confirmed_at=at + timedelta(minutes=1))
        first = self.manager.get("/management/reports/?start=2026-10-08&end=2026-10-08").json()
        second = self.manager.get("/management/reports/?start=2026-10-09&end=2026-10-09").json()
        assert first["totals"]["gross_cents"] == 1000 and first["totals"]["paid_cents"] == 0
        assert second["totals"]["gross_cents"] == 0 and second["totals"]["paid_cents"] == 1000
        self.venue.timezone = "America/New_York"
        from datetime import date
        a = business_boundary(self.venue, date(2026, 3, 7)).astimezone(dt_timezone.utc)
        b = business_boundary(self.venue, date(2026, 3, 8)).astimezone(dt_timezone.utc)
        assert (b - a).total_seconds() == 23 * 3600

    def test_cash_history_is_scoped_and_paginated(self):
        from modules.cash.models import CashPoint
        point = CashPoint.objects.create(venue=self.venue, label="Paged")
        staff = self.venue.staff_memberships.first().staff_member
        CashShift.objects.bulk_create([CashShift(venue=self.venue, cash_point=point, business_date=business_date(self.venue), opened_by=staff, status="CLOSED", opening_idempotency_key=f"page-{i}") for i in range(51)])
        path = f"/cash/shifts/history/?cash_point_id={point.id}"
        first = self.manager.get(path).json(); second = self.manager.get(path + "&offset=50").json()
        assert len(first["results"]) == 50 and first["next_offset"] == 50
        assert len(second["results"]) == 1 and second["next_offset"] is None
        assert not ({r["id"] for r in first["results"]} & {r["id"] for r in second["results"]})
        other = Venue.objects.create(name="Private", slug="private-history")
        other_point = CashPoint.objects.create(venue=other, label="Private")
        assert self.manager.get(f"/cash/shifts/history/?cash_point_id={other_point.id}").json()["results"] == []
        assert self.staff.get(path).status_code == 403


@skipUnless(connection.vendor == "postgresql", "Concurrent creation proof requires PostgreSQL")
class CatalogConcurrencyTests(HouseFixture, TransactionTestCase):
    def test_same_normalized_name_converges_under_concurrency(self):
        actor = ActorContext.from_session(StaffSession.objects.get(venue=self.venue, staff_member__login_identifier="house-manager"))
        barrier = Barrier(2)
        def create(name):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                product, created = resolve_or_create_product(actor=actor, name=name, price_cents=1500, fulfillment_station="KITCHEN")
                return str(product.id), created
            finally: connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            rows = list(pool.map(create, ["Omelete", "  OMELETE  "]))
        assert rows[0][0] == rows[1][0] and sum(row[1] for row in rows) == 1
        assert ProductIcon.objects.filter(product_id=rows[0][0]).count() == 1
