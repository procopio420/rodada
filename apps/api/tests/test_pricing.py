from django.db.models import Sum
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffSession, VenueStaffMembership
from modules.catalog.models import (
    ModifierGroup,
    ModifierOption,
    Product,
    ProductModifierGroup,
    ProductVariant,
)
from modules.ledger.models import Charge, LedgerAdjustment, Payment, PricingPolicy
from modules.ledger.pricing import allocate, percentage
from modules.ordering.models import Tab
from modules.venue.models import Venue


class CalculatorTests(SimpleTestCase):
    def test_rounding_and_allocation(self):
        self.assertEqual(percentage(3333, 1500), 500)
        self.assertEqual(percentage(5, 1000), 1)
        self.assertEqual(allocate(-2, {"c": 1, "b": 1, "a": 1}), {"c": 0, "b": -1, "a": -1})
        for basis in range(1, 101):
            for points in (0, 1, 3333, 5000, 9999, 10000):
                target = percentage(basis * 6, points)
                shares = allocate(-target, {"a": basis, "b": basis * 2, "c": basis * 3})
                self.assertEqual(sum(shares.values()), -target)
                self.assertTrue(
                    all(
                        -basis * (i + 1) <= shares[key] <= 0
                        for i, key in enumerate(("a", "b", "c"))
                    )
                )


class PricingFixture:
    def setUp(self):
        self.venue = Venue.objects.create(name="Pricing", slug="pricing")
        self.client = self.login("manager", "MANAGER")
        self.client.post("/auth/reauthenticate/", {"pin": "1234"}, format="json")
        self.product = Product.objects.create(
            venue=self.venue, name="Beer", price_cents=2000, fulfillment_station="BAR"
        )
        self.tab = Tab.objects.create(venue=self.venue, operating_limit_cents=100000)
        PricingPolicy.objects.create(
            venue=self.venue,
            service_enabled=True,
            service_basis_points=1000,
            service_opt_out=True,
            allow_post_payment=True,
        )
        order = self.client.post(
            f"/tabs/{self.tab.id}/orders/confirm/",
            {
                "idempotency_key": "order",
                "lines": [{"product_id": str(self.product.id), "quantity": 1}],
            },
            format="json",
        )
        assert order.status_code == 201, order.json()
        self.charge = Charge.objects.get(tab=self.tab)

    def login(self, identifier, role):
        staff = StaffMember.objects.create(display_name=identifier, login_identifier=identifier)
        staff.set_pin("1234")
        staff.save()
        VenueStaffMembership.objects.create(venue=self.venue, staff_member=staff, role=role)
        client = APIClient()
        result = client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": identifier,
                "pin": "1234",
                "installation_id": identifier,
                "platform": "WEB",
            },
            format="json",
        )
        assert result.status_code == 200, result.json()
        client.credentials(HTTP_AUTHORIZATION="Bearer " + result.json()["access_token"])
        return client

    def command(self, kind="TAB_DISCOUNT", value=100, **kwargs):
        self.tab.refresh_from_db()
        return {
            "kind": kind,
            "value": value,
            "expected_version": self.tab.version,
            "idempotency_key": f"{kind}-{LedgerAdjustment.objects.count()}",
            "reason_code": "CUSTOMER_REQUEST",
            **kwargs,
        }

    def apply(self, data, client=None, suffix=""):
        return (client or self.client).post(
            f"/tabs/{self.tab.id}/pricing/{suffix}", data, format="json"
        )

    def detail(self):
        return self.client.get(f"/tabs/{self.tab.id}/").json()

    def pay(self, value, key="payment"):
        return self.client.post(
            f"/tabs/{self.tab.id}/payments/",
            {"amount_cents": value, "method": "OTHER", "idempotency_key": key},
            format="json",
        )


class PricingTests(PricingFixture, TestCase):
    def test_preview_replay_allocation_and_original_history(self):
        data = self.command(
            "ITEM_DISCOUNT", 1000, charge_id=str(self.charge.id), calculation_type="PERCENTAGE"
        )
        self.assertEqual(self.apply(data, suffix="preview/").json()["after_payable_cents"], 1800)
        self.assertEqual(LedgerAdjustment.objects.count(), 0)
        result = self.apply(data)
        self.assertEqual(result.status_code, 200, result.json())
        self.assertEqual(self.apply(data).json(), result.json())
        self.assertEqual(self.apply({**data, "value": 2000}).json()["code"], "IDEMPOTENCY_CONFLICT")
        self.assertEqual(self.apply(self.command("SERVICE_CHARGE", 1000)).status_code, 200)
        detail = self.detail()
        self.assertEqual(
            (
                detail["original_subtotal_cents"],
                detail["discounts_cents"],
                detail["service_charge_cents"],
                detail["payable_cents"],
            ),
            (2000, 200, 180, 1980),
        )
        self.charge.refresh_from_db()
        self.assertEqual(self.charge.amount_cents, 2000)
        for fact in LedgerAdjustment.objects.all():
            self.assertEqual(
                fact.allocations.aggregate(v=Sum("amount_cents"))["v"], fact.amount_cents
            )

    def test_partial_payment_and_paid_courtesy_bounds(self):
        self.assertEqual(
            self.apply(self.command(value=2100)).json()["code"], "DISCOUNT_EXCEEDS_BASIS"
        )
        self.assertEqual(self.pay(1600).status_code, 201)
        self.assertEqual(
            self.apply(self.command(value=500)).json()["code"], "SETTLEMENT_CORRECTION_REQUIRED"
        )
        self.assertEqual(
            self.apply(self.command("COURTESY", 2000, charge_id=str(self.charge.id))).json()[
                "code"
            ],
            "SETTLEMENT_CORRECTION_REQUIRED",
        )
        self.assertEqual(self.apply(self.command(value=200)).json()["after_remaining_cents"], 200)
        self.assertEqual(Payment.objects.get().amount_cents, 1600)
        self.assertEqual(LedgerAdjustment.objects.count(), 1)

    def test_full_courtesy_reason(self):
        data = self.command("COURTESY", 2000, charge_id=str(self.charge.id), reason_code="")
        self.assertEqual(self.apply(data).json()["code"], "REASON_REQUIRED")
        self.assertEqual(self.apply({**data, "reason_code": "COMPLAINT"}).status_code, 200)
        self.assertEqual(self.detail()["courtesy_cents"], 2000)
        self.assertEqual(self.detail()["payable_cents"], 0)

    def test_approval_reauth_and_exact_replay(self):
        cashier = self.login("cashier", "CASHIER")
        data = self.command(value=600)
        self.assertEqual(self.apply(data, cashier).json()["code"], "APPROVAL_REQUIRED")
        result = self.apply(data, cashier, "approval-request/")
        self.assertEqual(result.status_code, 200, result.json())
        self.assertEqual(LedgerAdjustment.objects.count(), 0)
        url = f"/pricing/approvals/{result.json()['approval_id']}/approve/"
        session = StaffSession.objects.get(staff_member__login_identifier="manager")
        session.recently_reauthenticated_at = None
        session.save()
        self.assertEqual(self.client.post(url, {}, format="json").json()["code"], "REAUTH_REQUIRED")
        self.client.post("/auth/reauthenticate/", {"pin": "1234"}, format="json")
        first = self.client.post(url, {}, format="json")
        self.assertEqual(first.status_code, 200, first.json())
        self.assertEqual(self.client.post(url, {}, format="json").json(), first.json())
        fact = LedgerAdjustment.objects.get()
        self.assertEqual(fact.created_by.login_identifier, "cashier")
        self.assertEqual(fact.approved_by.login_identifier, "manager")

    def test_service_refresh_and_explicit_removal(self):
        self.assertEqual(self.apply(self.command("SERVICE_CHARGE", 1000)).status_code, 200)
        self.assertEqual(self.apply(self.command(value=200)).status_code, 200)
        self.assertEqual(self.pay(100).json()["code"], "SERVICE_REASSESSMENT_REQUIRED")
        self.assertEqual(self.apply(self.command("SERVICE_CHARGE", 1000)).status_code, 200)
        self.assertEqual(self.detail()["service_charge_cents"], 180)
        self.assertEqual(self.apply(self.command("SERVICE_CHARGE_REDUCTION", 180)).status_code, 200)
        self.assertEqual(self.detail()["service_charge_cents"], 0)
        self.assertEqual(self.pay(1800).status_code, 201)
        self.assertEqual(LedgerAdjustment.objects.filter(kind="SERVICE_CHARGE").count(), 2)

    def test_policy_and_staff_threshold(self):
        staff = self.login("staff", "STAFF")
        self.assertEqual(
            self.apply(self.command(value=1), staff).json()["code"], "APPROVAL_REQUIRED"
        )
        policy = self.client.get("/pricing/policy/").json()
        policy["expected_version"] = policy.pop("version")
        policy["service_basis_points"] = 750
        self.assertEqual(
            self.client.put("/pricing/policy/", policy, format="json").status_code, 200
        )
        self.assertEqual(
            self.client.put("/pricing/policy/", policy, format="json").status_code, 409
        )
        data = self.command("SERVICE_CHARGE")
        del data["value"]
        self.assertEqual(self.apply(data).json()["effect_cents"], 150)
        other = Venue.objects.create(name="Other", slug="other")
        foreign = Tab.objects.create(venue=other)
        self.assertEqual(self.client.get(f"/tabs/{foreign.id}/pricing/").status_code, 404)

    def test_reverse_and_net_refund_preview(self):
        applied = self.apply(self.command(value=400)).json()
        self.pay(1600)
        helper = self.client.get(
            f"/tabs/{self.tab.id}/pricing/refund-preview/{self.charge.id}/"
        ).json()
        self.assertEqual(helper["maximum_refund_cents"], 1600)
        data = self.command("REVERSAL", 0, adjustment_id=applied["adjustment_id"])
        first = self.apply(data)
        self.assertEqual(first.json()["after_remaining_cents"], 400)
        self.assertEqual(self.apply(data).json(), first.json())
        self.assertEqual(
            self.apply(self.command("REVERSAL", 0, adjustment_id=applied["adjustment_id"])).json()[
                "code"
            ],
            "ALREADY_REVERSED",
        )

    def test_inflight_version_and_limit(self):
        data = self.command()
        self.apply(data)
        data["idempotency_key"] = "another"
        self.assertEqual(self.apply(data).json()["code"], "VERSION_CONFLICT")
        Payment.objects.create(
            tab=self.tab,
            amount_cents=100,
            method="PIX",
            status="CONFIRMATION_PENDING",
            provider="fake",
            received_by=StaffMember.objects.get(login_identifier="manager"),
            idempotency_key="pending",
        )
        self.assertEqual(self.apply(self.command()).json()["code"], "PAYMENT_IN_FLIGHT")

    def test_unpaid_split_conserves_components(self):
        self.apply(self.command(value=200))
        self.apply(self.command("SERVICE_CHARGE", 1000))
        dest = Tab.objects.create(venue=self.venue, operating_limit_cents=100000)
        self.tab.refresh_from_db()
        data = {
            "kind": "MOVE_ITEMS",
            "expected_version": self.tab.version,
            "destination_version": dest.version,
            "destination_tab_id": str(dest.id),
            "idempotency_key": "split",
            "reason": "SHARE",
            "lines": [{"charge_id": str(self.charge.id), "amount_cents": 990}],
        }
        result = self.client.post(f"/tabs/{self.tab.id}/operations/", data, format="json")
        self.assertEqual(result.status_code, 200, result.json())
        source, target = self.detail(), self.client.get(f"/tabs/{dest.id}/").json()
        for key, expected in (
            ("payable_cents", 1980),
            ("original_subtotal_cents", 2000),
            ("discounts_cents", 200),
            ("service_charge_cents", 180),
        ):
            self.assertEqual(source[key] + target[key], expected)
        self.assertFalse(source["service_assessment_stale"])
        self.assertEqual(self.pay(100).status_code, 201)
        self.tab.refresh_from_db()
        dest.refresh_from_db()
        data.update(
            expected_version=self.tab.version,
            destination_version=dest.version,
            idempotency_key="paid-transfer",
        )
        self.assertEqual(
            self.client.post(f"/tabs/{self.tab.id}/operations/", data, format="json").json()[
                "code"
            ],
            "CONFIRMED_PAYMENT",
        )

    def test_customized_bill_correction_and_management(self):
        variant = ProductVariant.objects.create(
            product=self.product, name="Large", price_cents=2500
        )
        group = ModifierGroup.objects.create(
            venue=self.venue,
            name="Extras",
            selection_mode="MULTI",
            min_selections=0,
            max_selections=2,
        )
        ProductModifierGroup.objects.create(product=self.product, group=group)
        option = ModifierOption.objects.create(group=group, name="Extra", price_delta_cents=300)
        result = self.client.post(
            f"/tabs/{self.tab.id}/orders/confirm/",
            {
                "idempotency_key": "custom",
                "lines": [
                    {
                        "product_id": str(self.product.id),
                        "quantity": 1,
                        "variant_id": str(variant.id),
                        "modifier_option_ids": [str(option.id)],
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(result.status_code, 201, result.json())
        self.assertEqual(self.apply(self.command(value=800)).status_code, 200)
        self.assertEqual(self.apply(self.command("SERVICE_CHARGE", 1000)).status_code, 200)
        self.assertEqual(self.pay(2000).status_code, 201)
        customized_item = result.json()["items"][0]["id"]
        for state in ("ACCEPTED", "PREPARING"):
            transition = self.client.post(
                f"/order-items/{customized_item}/transition/", {"state": state}, format="json"
            )
            self.assertEqual(transition.status_code, 200, transition.json())
        remake = self.client.post(
            f"/order-items/{customized_item}/corrections/post-production/",
            {"kind": "REMAKE", "reason_code": "STATION_MISTAKE", "idempotency_key": "remake"},
            format="json",
        )
        self.assertEqual(remake.status_code, 201, remake.json())
        self.assertEqual(
            self.apply(self.command("COURTESY", 400, charge_id=str(self.charge.id))).status_code,
            200,
        )
        self.assertEqual(self.apply(self.command("SERVICE_CHARGE", 1000)).status_code, 200)
        self.assertEqual(self.pay(1960, "final").status_code, 201)
        self.assertEqual(
            self.client.post(f"/tabs/{self.tab.id}/close/", {}, format="json").status_code, 200
        )
        from modules.venue.calendar import business_date

        day = business_date(self.venue)
        report = self.client.get(f"/management/reports/?start={day}&end={day}").json()["totals"]
        self.assertEqual(
            tuple(
                report[k]
                for k in (
                    "gross_cents",
                    "tab_discounts_cents",
                    "courtesy_cents",
                    "net_consumption_cents",
                    "service_pass_through_cents",
                    "payable_cents",
                    "net_received_cents",
                )
            ),
            (7600, 800, 3200, 3600, 360, 3960, 3960),
        )
        self.assertEqual(report["current_open_exposure_cents"], 0)
        self.assertEqual(Charge.objects.aggregate(v=Sum("amount_cents"))["v"], 7600)

    def test_multiple_items_rounding_is_persisted(self):
        from modules.ordering.models import Order, OrderItem

        order = Order.objects.create(tab=self.tab)
        for i in range(3):
            item = OrderItem.objects.create(
                order=order,
                product=self.product,
                product_name_snapshot="Odd",
                unit_price_cents=333,
                quantity=1,
            )
            Charge.objects.create(tab=self.tab, order_item=item, amount_cents=333)
        result = self.apply(self.command(value=3333, calculation_type="PERCENTAGE"))
        self.assertEqual(result.json()["effect_cents"], -1000)
        fact = LedgerAdjustment.objects.get(pk=result.json()["adjustment_id"])
        self.assertEqual(sum(a.amount_cents for a in fact.allocations.all()), -1000)
        self.assertEqual(self.detail()["payable_cents"], 1999)

    def test_post_payment_policy_and_required_reason(self):
        self.pay(100)
        PricingPolicy.objects.filter(venue=self.venue).update(allow_post_payment=False)
        self.assertEqual(self.apply(self.command()).json()["code"], "POST_PAYMENT_DISABLED")
        PricingPolicy.objects.filter(venue=self.venue).update(allow_post_payment=True)
        self.assertEqual(self.apply(self.command(reason_code="")).json()["code"], "REASON_REQUIRED")
        self.assertEqual(LedgerAdjustment.objects.count(), 0)

    def test_service_disabled_maximum_and_house_exposure(self):
        policy = PricingPolicy.objects.get(venue=self.venue)
        policy.service_enabled = False
        policy.save()
        self.assertEqual(
            self.apply(self.command("SERVICE_CHARGE", 1000)).json()["code"],
            "SERVICE_POLICY_REQUIRED",
        )
        policy.service_enabled = True
        policy.service_max_basis_points = 500
        policy.save()
        self.assertEqual(
            self.apply(self.command("SERVICE_CHARGE", 1000)).json()["code"],
            "SERVICE_POLICY_REQUIRED",
        )
        self.tab.operating_limit_cents = 2000
        self.tab.save()
        self.assertEqual(
            self.apply(self.command("SERVICE_CHARGE", 500)).json()["code"],
            "SPENDING_LIMIT_EXCEEDED",
        )
        self.assertEqual(self.apply(self.command(value=200)).status_code, 200)
        self.assertEqual(self.detail()["remaining_capacity_cents"], 200)

    def test_refund_after_discount_preserves_pricing(self):
        self.apply(self.command(value=400))
        payment = self.pay(1600).json()
        result = self.client.post(
            f"/payments/{payment['id']}/refunds/",
            {"amount_cents": 600, "idempotency_key": "refund", "reason": "CUSTOMER_REQUEST"},
            format="json",
        )
        self.assertEqual(result.status_code, 201, result.json())
        detail = self.detail()
        self.assertEqual(
            (detail["payable_cents"], detail["refunds_cents"], detail["exposure_cents"]),
            (1600, 600, 600),
        )
        self.assertEqual(Payment.objects.get().amount_cents, 1600)
        self.assertEqual(LedgerAdjustment.objects.count(), 1)

    def test_stale_payment_version_is_rejected(self):
        self.tab.refresh_from_db()
        version = self.tab.version
        self.apply(self.command(value=100))
        result = self.client.post(
            f"/tabs/{self.tab.id}/payments/",
            {
                "amount_cents": 100,
                "method": "OTHER",
                "idempotency_key": "stale",
                "expected_version": version,
            },
            format="json",
        )
        self.assertEqual(result.json()["code"], "VERSION_CONFLICT")
        self.assertEqual(Payment.objects.count(), 0)

    def test_stale_approval_never_applies(self):
        cashier = self.login("cashier", "CASHIER")
        data = self.command(value=600)
        requested = self.apply(data, cashier, "approval-request/").json()
        self.apply(self.command(value=100, idempotency_key="intervening"))
        self.assertEqual(self.apply(data, cashier, "approval-request/").json(), requested)
        response = self.client.post(
            f"/pricing/approvals/{requested['approval_id']}/approve/", {}, format="json"
        )
        self.assertEqual(response.json()["code"], "VERSION_CONFLICT")
        self.assertEqual(LedgerAdjustment.objects.count(), 1)

    def test_service_reduction_reversal_and_reason_authority(self):
        self.apply(self.command("SERVICE_CHARGE", 750))
        result = self.apply(self.command("SERVICE_CHARGE_REDUCTION", 50)).json()
        self.assertEqual(self.detail()["service_charge_cents"], 100)
        self.assertEqual(
            self.apply(
                self.command("REVERSAL", 0, adjustment_id=result["adjustment_id"])
            ).status_code,
            200,
        )
        self.assertEqual(self.detail()["service_charge_cents"], 150)
        PricingPolicy.objects.filter(venue=self.venue).update(service_opt_out=False)
        staff = self.login("staff", "STAFF")
        data = self.command("SERVICE_CHARGE_REDUCTION", 50)
        self.assertEqual(self.apply(data, staff).json()["code"], "APPROVAL_REQUIRED")

    def test_configurable_cashier_service_removal_approval(self):
        self.assertEqual(self.apply(self.command("SERVICE_CHARGE", 1000)).status_code, 200)
        PricingPolicy.objects.filter(venue=self.venue).update(service_opt_out=False)
        cashier = self.login("cashier", "CASHIER")
        command = self.command("SERVICE_CHARGE_REDUCTION", 50)
        self.assertEqual(self.apply(command, cashier).json()["code"], "APPROVAL_REQUIRED")
        self.assertEqual(self.detail()["service_charge_cents"], 200)
        PricingPolicy.objects.filter(venue=self.venue).update(service_removal_requires_manager=False)
        self.assertEqual(self.apply(command, cashier).status_code, 200)
        self.assertEqual(self.detail()["service_charge_cents"], 150)

    def test_discounted_unpaid_cancellation_uses_net(self):
        self.apply(self.command("ITEM_DISCOUNT", 500, charge_id=str(self.charge.id)))
        item = self.charge.order_item
        response = self.client.post(
            f"/order-items/{item.id}/corrections/cancel/",
            {
                "kind": "WRONG_ITEM_ENTERED",
                "reason_code": "WRONG_ITEM",
                "idempotency_key": "cancel",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())
        self.assertEqual(self.detail()["exposure_cents"], 0)
        self.assertEqual(
            LedgerAdjustment.objects.get(kind="ORDER_ITEM_CANCELLATION").amount_cents, -1500
        )

    def test_service_removal_preserves_original_treatment_after_policy_change(self):
        PricingPolicy.objects.filter(venue=self.venue).update(service_treatment="REVENUE")
        self.assertEqual(self.apply(self.command("SERVICE_CHARGE", 1000)).status_code, 200)
        PricingPolicy.objects.filter(venue=self.venue).update(service_treatment="PASS_THROUGH")
        self.assertEqual(self.apply(self.command("SERVICE_CHARGE_REDUCTION", 200)).status_code, 200)
        from modules.venue.calendar import business_date
        day = business_date(self.venue)
        report = self.client.get(f"/management/reports/?start={day}&end={day}").json()["totals"]
        self.assertEqual(report["service_revenue_cents"], 0)
        self.assertEqual(report["service_pass_through_cents"], 0)
        self.assertEqual(report["net_sales_cents"], 2000)
