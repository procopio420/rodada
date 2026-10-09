from django.test import TestCase
from rest_framework.test import APIClient

from modules.access.models import StaffMember, VenueStaffMembership
from modules.catalog.models import (
    ModifierGroup,
    ModifierOption,
    Product,
    ProductModifierGroup,
    ProductVariant,
)
from modules.hospitality.models import Table
from modules.ledger.models import Charge
from modules.ordering.models import OrderItem, Tab
from modules.venue.models import Venue


class CustomizationTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Aderlan", slug="customization")
        self.staff = StaffMember.objects.create(
            display_name="Manager", login_identifier="custom-manager"
        )
        self.staff.set_pin("1234")
        self.staff.save()
        self.membership = VenueStaffMembership.objects.create(
            venue=self.venue, staff_member=self.staff, role="MANAGER"
        )
        self.client = APIClient()
        login = self.client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": self.staff.login_identifier,
                "pin": "1234",
                "installation_id": "custom-test",
                "platform": "WEB",
            },
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
        created = self.client.post(
            "/catalog/resolve-or-create/",
            {"name": "Hambúrguer", "price_cents": 2000, "fulfillment_station": "KITCHEN"},
            format="json",
        )
        assert created.status_code == 201, created.json()
        self.product = Product.objects.get(pk=created.json()["product"]["id"])
        self.tab = Tab.objects.create(venue=self.venue, operating_limit_cents=100000)
        self.simple = self.configure(
            "variant", {"name": "Simples", "price_cents": 2000, "is_default": True}
        )
        self.double = self.configure("variant", {"name": "Duplo", "price_cents": 3000})
        self.cooking = self.configure(
            "group",
            {"name": "Ponto", "selection_mode": "SINGLE", "min_selections": 1, "max_selections": 1},
        )
        self.medium = self.configure("option", {"name": "Ao ponto"}, group_id=self.cooking)
        self.rare = self.configure("option", {"name": "Malpassado"}, group_id=self.cooking)
        self.additions = self.configure(
            "group",
            {
                "name": "Adicionais",
                "selection_mode": "MULTI",
                "min_selections": 0,
                "max_selections": 2,
            },
        )
        self.bacon = self.configure(
            "option",
            {"name": "Bacon", "price_delta_cents": 500, "semantic_kind": "ADD"},
            group_id=self.additions,
        )
        self.cheese = self.configure(
            "option",
            {"name": "Queijo", "price_delta_cents": 300, "semantic_kind": "ADD"},
            group_id=self.additions,
        )
        self.onion = self.configure(
            "option", {"name": "Sem cebola", "semantic_kind": "REMOVE"}, group_id=self.additions
        )

    def configure(self, kind, values, **extra):
        result = self.client.post(
            f"/catalog/products/{self.product.id}/customization/",
            {"kind": kind, "values": values, **extra},
            format="json",
        )
        assert result.status_code == 200, result.json()
        return result.json()["id"]

    def line(self, **overrides):
        return {
            "product_id": str(self.product.id),
            "quantity": 2,
            "variant_id": self.double,
            "modifier_option_ids": [self.medium, self.bacon, self.cheese],
            "special_instructions": "Molho separado",
            **overrides,
        }

    def confirm(self, line=None, key="burger"):
        return self.client.post(
            f"/tabs/{self.tab.id}/orders/confirm/",
            {"idempotency_key": key, "lines": [line or self.line()]},
            format="json",
        )

    def test_complete_persisted_burger_guest_kitchen_and_availability(self):
        first = self.confirm()
        assert first.status_code == 201, first.json()
        item = first.json()["items"][0]
        assert item["unit_price_cents"] == 3800
        assert item["line_total_cents"] == 7600
        replay = self.confirm()
        assert replay.status_code == 200 and replay.json()["id"] == first.json()["id"]
        assert Charge.objects.count() == 1
        queue = self.client.get("/production/KITCHEN/").json()["results"][0]
        assert queue["customization_snapshot"] == item["customization_snapshot"]
        table = Table.objects.create(venue=self.venue, label="27", guest_ordering_mode="DIRECT")
        guest = APIClient()
        token = guest.post(
            "/guest/qr/resolve/", {"token": table.public_token}, format="json"
        ).json()["guest_session_token"]
        guest.credentials(HTTP_X_GUEST_SESSION=token)
        tab = guest.post("/guest/tabs/", {}, format="json").json()
        Tab.objects.filter(pk=tab["id"]).update(operating_limit_cents=10000)
        menu = guest.get("/guest/catalog/").json()["results"][0]
        staff_menu = self.client.get("/catalog/products/").json()["results"][0]
        assert menu["variants"] == staff_menu["variants"]
        assert menu["modifier_groups"] == staff_menu["modifier_groups"]
        result = guest.post(
            "/guest/orders/confirm/",
            {"idempotency_key": "guest-burger", "lines": [self.line()]},
            format="json",
        )
        assert result.status_code == 201, result.json()
        assert result.json()["items"][0]["customization_snapshot"] == item["customization_snapshot"]
        unavailable = self.client.post(
            f"/catalog/products/{self.product.id}/customization/option/{self.bacon}/availability/",
            {"state": "UNAVAILABLE", "expected_version": 1, "reason": "Acabou"},
            format="json",
        )
        assert unavailable.status_code == 200, unavailable.json()
        stale = self.confirm(key="new-burger")
        assert stale.status_code == 409 and stale.json()["code"] == "MODIFIER_UNAVAILABLE"
        assert stale.json()["option_id"] == self.bacon
        assert self.confirm().status_code == 200
        Option = ModifierOption.objects.get(pk=self.bacon)
        Option.name = "Bacon novo"
        Option.price_delta_cents = 900
        Option.save()
        ProductVariant.objects.filter(pk=self.double).delete()
        Option.delete()
        self.product.name = "Burger novo"
        self.product.fulfillment_station = "BAR"
        self.product.save()
        persisted = OrderItem.objects.get(pk=item["id"])
        assert persisted.customization_snapshot == item["customization_snapshot"]
        assert self.client.get("/production/KITCHEN/").json()["results"][0]["id"] == item["id"]
        position = self.client.get(f"/tabs/{self.tab.id}/").json()
        assert position["exposure_cents"] == 7600
        payment = self.client.post(
            f"/tabs/{self.tab.id}/payments/",
            {"amount_cents": 3000, "method": "EXTERNAL_TERMINAL", "idempotency_key": "partial"},
            format="json",
        )
        assert payment.status_code == 201, payment.json()
        assert self.client.get(f"/tabs/{self.tab.id}/").json()["exposure_cents"] == 4600
        assert (
            self.client.post("/auth/reauthenticate/", {"pin": "1234"}, format="json").status_code
            == 200
        )
        refund_path = f"/payments/{payment.json()['id']}/refunds/"
        refund_payload = {
            "amount_cents": 1000,
            "idempotency_key": "custom-refund",
            "reason": "Conferência",
        }
        refund = self.client.post(refund_path, refund_payload, format="json")
        assert refund.status_code == 201, refund.json()
        replay = self.client.post(refund_path, refund_payload, format="json")
        assert replay.status_code == 200 and replay.json()["id"] == refund.json()["id"]
        assert self.client.get(f"/tabs/{self.tab.id}/").json()["exposure_cents"] == 5600

    def test_validation_rejects_entire_order(self):
        cases = [
            ({"variant_id": None}, "VARIANT_REQUIRED"),
            ({"modifier_option_ids": []}, "MODIFIER_REQUIRED"),
            ({"modifier_option_ids": [self.medium, self.rare]}, "TOO_MANY_MODIFIERS"),
            (
                {"modifier_option_ids": [self.medium, self.bacon, self.cheese, self.onion]},
                "TOO_MANY_MODIFIERS",
            ),
            ({"modifier_option_ids": [self.medium, self.medium]}, "INVALID_MODIFIER_SELECTION"),
        ]
        for values, code in cases:
            with self.subTest(code=code):
                result = self.confirm(self.line(**values))
                assert result.status_code == 409 and result.json()["code"] == code, result.json()
        assert not OrderItem.objects.exists() and not Charge.objects.exists()

    def test_limit_includes_modifiers_and_ignores_client_price(self):
        self.tab.operating_limit_cents = 7000
        self.tab.save()
        rejected = self.confirm(self.line(unit_price_cents=1))
        assert rejected.status_code == 409 and rejected.json()["requested_cents"] == 7600
        assert not Charge.objects.exists()

    def test_variant_parent_and_option_active_gates(self):
        ProductVariant.objects.filter(pk=self.double).update(availability="UNAVAILABLE")
        assert self.confirm().json()["code"] == "VARIANT_UNAVAILABLE"
        ProductVariant.objects.filter(pk=self.double).update(availability="AVAILABLE")
        ModifierOption.objects.filter(pk=self.cheese).update(active=False)
        assert self.confirm().json()["code"] == "MODIFIER_UNAVAILABLE"
        self.product.active = False
        self.product.save()
        assert self.confirm().json()["code"] == "PRODUCTS_NOT_CONFIRMABLE"

    def test_configuration_changes_idempotency_intent(self):
        assert self.confirm().status_code == 201
        changed = self.confirm(self.line(modifier_option_ids=[self.medium, self.bacon]))
        assert changed.status_code == 409 and changed.json()["code"] == "IDEMPOTENCY_CONFLICT"
        assert Charge.objects.count() == 1

    def test_cross_venue_and_permissions_and_optimistic_versions(self):
        other = Venue.objects.create(name="Outro", slug="custom-other")
        group = ModifierGroup.objects.create(venue=other, name="Outro", selection_mode="SINGLE")
        result = self.client.post(
            f"/catalog/products/{self.product.id}/customization/",
            {"kind": "attach", "group_id": str(group.id)},
            format="json",
        )
        assert result.status_code == 404
        assert (
            self.client.post(
                f"/catalog/products/{self.product.id}/customization/",
                {
                    "kind": "group",
                    "id": self.cooking,
                    "expected_version": 9,
                    "values": {"name": "Changed"},
                },
                format="json",
            ).status_code
            == 409
        )
        self.membership.role = "STAFF"
        self.membership.save()
        assert (
            self.client.post(
                f"/catalog/products/{self.product.id}/customization/",
                {"kind": "variant", "values": {"name": "Bad", "price_cents": 1}},
                format="json",
            ).status_code
            == 403
        )
        availability = (
            f"/catalog/products/{self.product.id}/customization/option/{self.bacon}/availability/"
        )
        assert (
            self.client.post(
                availability, {"state": "UNAVAILABLE", "expected_version": 1}, format="json"
            ).status_code
            == 403
        )
        self.membership.capability_overrides = {"allow": ["catalog.availability.kitchen"]}
        self.membership.save()
        assert (
            self.client.post(
                availability, {"state": "UNAVAILABLE", "expected_version": 1}, format="json"
            ).status_code
            == 200
        )
        assert (
            self.client.post(
                availability, {"state": "AVAILABLE", "expected_version": 1}, format="json"
            ).status_code
            == 409
        )

    def test_zero_price_removal_and_simple_product(self):
        result = self.confirm(self.line(modifier_option_ids=[self.medium, self.onion], quantity=1))
        assert result.json()["items"][0]["unit_price_cents"] == 3000
        assert (
            result.json()["items"][0]["customization_snapshot"]["modifiers"][-1]["semantic_kind"]
            == "REMOVE"
        )
        simple = Product.objects.create(
            venue=self.venue, name="Água", price_cents=501, fulfillment_station="BAR"
        )
        result = self.confirm({"product_id": str(simple.id), "quantity": 3}, key="water")
        assert result.status_code == 201 and result.json()["items"][0]["line_total_cents"] == 1503

    def test_minimum_multi_and_foreign_option_and_http_note_length(self):
        ModifierGroup.objects.filter(pk=self.additions).update(min_selections=2)
        result = self.confirm(self.line(modifier_option_ids=[self.medium, self.bacon]))
        assert result.json()["code"] == "MODIFIER_REQUIRED"
        other = Venue.objects.create(name="Other", slug="option-other")
        group = ModifierGroup.objects.create(venue=other, name="Foreign", selection_mode="SINGLE")
        option = ModifierOption.objects.create(group=group, name="Foreign")
        result = self.confirm(
            self.line(modifier_option_ids=[self.medium, self.bacon, self.cheese, str(option.pk)])
        )
        assert result.json()["code"] == "INVALID_MODIFIER_SELECTION"
        assert self.confirm(self.line(special_instructions="x" * 501)).status_code == 400
        assert (
            self.client.post(
                f"/catalog/products/{self.product.id}/customization/",
                {
                    "kind": "option",
                    "group_id": self.additions,
                    "values": {"name": "Discount", "price_delta_cents": -1},
                },
                format="json",
            ).status_code
            == 400
        )

    def test_snapshot_fields_cannot_be_mutated_through_model_save(self):
        from django.core.exceptions import ValidationError

        assert self.confirm().status_code == 201
        item = OrderItem.objects.get()
        item.customization_snapshot["modifiers"][0]["name"] = "Changed"
        with self.assertRaises(ValidationError):
            item.save()
        item.refresh_from_db()
        item.state = "ACCEPTED"
        item.save(update_fields=["state"])
        assert item.customization_snapshot["modifiers"][0]["name"] == "Ao ponto"

    def test_default_variant_unique_and_group_priority(self):
        self.configure("variant", {"is_default": True}, id=self.double, expected_version=1)
        assert (
            ProductVariant.objects.filter(
                product=self.product, active=True, is_default=True
            ).count()
            == 1
        )
        self.configure(
            "group", {"name": "Ponto"}, id=self.cooking, expected_version=1, display_order=12
        )
        assert (
            ProductModifierGroup.objects.get(product=self.product, group_id=self.cooking).sort_order
            == 12
        )

    def test_remake_preserves_configuration_without_second_exposure(self):
        result = self.confirm()
        item = result.json()["items"][0]
        for state in ("ACCEPTED", "PREPARING"):
            assert (
                self.client.post(
                    f"/order-items/{item['id']}/transition/", {"state": state}, format="json"
                ).status_code
                == 200
            )
        assert (
            self.client.post("/auth/reauthenticate/", {"pin": "1234"}, format="json").status_code
            == 200
        )
        remake = self.client.post(
            f"/order-items/{item['id']}/corrections/post-production/",
            {
                "kind": "REMAKE",
                "reason_code": "STATION_MISTAKE",
                "idempotency_key": "custom-remake",
            },
            format="json",
        )
        assert remake.status_code == 201, remake.json()
        replacement = OrderItem.objects.get(pk=remake.json()["replacement_order_item_id"])
        assert replacement.customization_snapshot == item["customization_snapshot"]
        assert replacement.fulfillment_station_snapshot == "KITCHEN"
        assert self.client.get(f"/tabs/{self.tab.id}/").json()["exposure_cents"] == 7600

    def test_pre_upgrade_simple_order_fingerprint_still_replays(self):
        import hashlib
        import json

        from modules.ordering.models import Order

        water = Product.objects.create(
            venue=self.venue, name="Legacy water", price_cents=1250, fulfillment_station="BAR"
        )
        fingerprint = hashlib.sha256(
            json.dumps(
                {"source": "STAFF", "lines": [(str(water.pk), 2)]},
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode()
        ).hexdigest()
        order = Order.objects.create(
            tab=self.tab, source="STAFF", idempotency_key="legacy", request_fingerprint=fingerprint
        )
        item = OrderItem.objects.create(
            order=order,
            product=water,
            product_name_snapshot="Legacy water",
            unit_price_cents=1250,
            quantity=2,
        )
        Charge.objects.create(tab=self.tab, order_item=item, amount_cents=2500)
        response = self.confirm({"product_id": str(water.pk), "quantity": 2}, key="legacy")
        assert response.status_code == 200 and response.json()["id"] == str(order.pk)
        assert Charge.objects.count() == 1 and OrderItem.objects.count() == 1
