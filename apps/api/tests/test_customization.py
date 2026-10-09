from django.test import TestCase
from rest_framework.test import APIClient
from modules.access.models import StaffMember, VenueStaffMembership
from modules.catalog.models import Product, ProductVariant, ModifierGroup, ModifierOption, ProductModifierGroup
from modules.ordering.models import Tab, OrderItem
from modules.ledger.models import Charge
from modules.hospitality.models import Table
from modules.venue.models import Venue


class CustomizationTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Aderlan", slug="customization")
        self.staff = StaffMember.objects.create(display_name="Manager", login_identifier="custom-manager")
        self.staff.set_pin("1234")
        self.staff.save()
        self.membership = VenueStaffMembership.objects.create(venue=self.venue, staff_member=self.staff, role="MANAGER")
        self.client = APIClient()
        login = self.client.post('/auth/login/', {"venue_slug": self.venue.slug, "login_identifier": self.staff.login_identifier, "pin": "1234", "installation_id": "custom-test", "platform": "WEB"}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
        created = self.client.post('/catalog/resolve-or-create/', {"name": "Hambúrguer", "price_cents": 2000, "fulfillment_station": "KITCHEN"}, format="json")
        assert created.status_code == 201, created.json()
        self.product = Product.objects.get(pk=created.json()["product"]["id"])
        self.tab = Tab.objects.create(venue=self.venue, operating_limit_cents=100000)
        self.simple = self.configure("variant", {"name": "Simples", "price_cents": 2000, "is_default": True})
        self.double = self.configure("variant", {"name": "Duplo", "price_cents": 3000})
        self.cooking = self.configure("group", {"name": "Ponto", "selection_mode": "SINGLE", "min_selections": 1, "max_selections": 1})
        self.medium = self.configure("option", {"name": "Ao ponto"}, group_id=self.cooking)
        self.rare = self.configure("option", {"name": "Malpassado"}, group_id=self.cooking)
        self.additions = self.configure("group", {"name": "Adicionais", "selection_mode": "MULTI", "min_selections": 0, "max_selections": 2})
        self.bacon = self.configure("option", {"name": "Bacon", "price_delta_cents": 500, "semantic_kind": "ADD"}, group_id=self.additions)
        self.cheese = self.configure("option", {"name": "Queijo", "price_delta_cents": 300, "semantic_kind": "ADD"}, group_id=self.additions)
        self.onion = self.configure("option", {"name": "Sem cebola", "semantic_kind": "REMOVE"}, group_id=self.additions)

    def configure(self, kind, values, **extra):
        result = self.client.post(f'/catalog/products/{self.product.id}/customization/', {"kind": kind, "values": values, **extra}, format="json")
        assert result.status_code == 200, result.json()
        return result.json()["id"]

    def line(self, **overrides):
        return {"product_id": str(self.product.id), "quantity": 2, "variant_id": self.double, "modifier_option_ids": [self.medium, self.bacon, self.cheese], "special_instructions": "Molho separado", **overrides}

    def confirm(self, line=None, key="burger"):
        return self.client.post(f'/tabs/{self.tab.id}/orders/confirm/', {"idempotency_key": key, "lines": [line or self.line()]}, format="json")

    def test_complete_persisted_burger_guest_kitchen_and_availability(self):
        first = self.confirm()
        assert first.status_code == 201, first.json()
        item = first.json()["items"][0]
        assert item["unit_price_cents"] == 3800
        assert item["line_total_cents"] == 7600
        replay = self.confirm()
        assert replay.status_code == 200 and replay.json()["id"] == first.json()["id"]
        assert Charge.objects.count() == 1
        queue = self.client.get('/production/KITCHEN/').json()["results"][0]
        assert queue["customization_snapshot"] == item["customization_snapshot"]
        table = Table.objects.create(venue=self.venue, label="27", guest_ordering_mode="DIRECT")
        guest = APIClient()
        token = guest.post('/guest/qr/resolve/', {"token": table.public_token}, format="json").json()["guest_session_token"]
        guest.credentials(HTTP_X_GUEST_SESSION=token)
        tab = guest.post('/guest/tabs/', {}, format="json").json()
        Tab.objects.filter(pk=tab["id"]).update(operating_limit_cents=10000)
        menu = guest.get('/guest/catalog/').json()["results"][0]
        staff_menu = self.client.get('/catalog/products/').json()["results"][0]
        assert menu["variants"] == staff_menu["variants"]
        assert menu["modifier_groups"] == staff_menu["modifier_groups"]
        result = guest.post('/guest/orders/confirm/', {"idempotency_key": "guest-burger", "lines": [self.line()]}, format="json")
        assert result.status_code == 201, result.json()
        assert result.json()["items"][0]["customization_snapshot"] == item["customization_snapshot"]
        unavailable = self.client.post(f'/catalog/products/{self.product.id}/customization/option/{self.bacon}/availability/', {"state": "UNAVAILABLE", "expected_version": 1, "reason": "Acabou"}, format="json")
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
        assert self.client.get('/production/KITCHEN/').json()["results"][0]["id"] == item["id"]
        position = self.client.get(f'/tabs/{self.tab.id}/').json()
        assert position["exposure_cents"] == 7600
        payment = self.client.post(f'/tabs/{self.tab.id}/payments/', {"amount_cents": 3000, "method": "EXTERNAL_TERMINAL", "idempotency_key": "partial"}, format="json")
        assert payment.status_code == 201, payment.json()
        assert self.client.get(f'/tabs/{self.tab.id}/').json()["exposure_cents"] == 4600

    def test_validation_rejects_entire_order(self):
        cases = [({"variant_id": None}, "VARIANT_REQUIRED"),
            ({"modifier_option_ids": []}, "MODIFIER_REQUIRED"),
            ({"modifier_option_ids": [self.medium, self.rare]}, "TOO_MANY_MODIFIERS"),
            ({"modifier_option_ids": [self.medium, self.bacon, self.cheese, self.onion]}, "TOO_MANY_MODIFIERS"),
            ({"modifier_option_ids": [self.medium, self.medium]}, "INVALID_MODIFIER_SELECTION")]
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
        result = self.client.post(f'/catalog/products/{self.product.id}/customization/', {"kind": "attach", "group_id": str(group.id)}, format="json")
        assert result.status_code == 404
        assert self.client.post(f'/catalog/products/{self.product.id}/customization/', {"kind": "group", "id": self.cooking, "expected_version": 9, "values": {"name": "Changed"}}, format="json").status_code == 409
        self.membership.role = "STAFF"
        self.membership.save()
        assert self.client.post(f'/catalog/products/{self.product.id}/customization/', {"kind": "variant", "values": {"name": "Bad", "price_cents": 1}}, format="json").status_code == 403
        availability = f'/catalog/products/{self.product.id}/customization/option/{self.bacon}/availability/'
        assert self.client.post(availability, {"state": "UNAVAILABLE", "expected_version": 1}, format="json").status_code == 403
        self.membership.capability_overrides = {"allow": ["catalog.availability.kitchen"]}
        self.membership.save()
        assert self.client.post(availability, {"state": "UNAVAILABLE", "expected_version": 1}, format="json").status_code == 200
        assert self.client.post(availability, {"state": "AVAILABLE", "expected_version": 1}, format="json").status_code == 409

    def test_zero_price_removal_and_simple_product(self):
        result = self.confirm(self.line(modifier_option_ids=[self.medium, self.onion], quantity=1))
        assert result.json()["items"][0]["unit_price_cents"] == 3000
        assert result.json()["items"][0]["customization_snapshot"]["modifiers"][-1]["semantic_kind"] == "REMOVE"
        simple = Product.objects.create(venue=self.venue, name="Água", price_cents=501, fulfillment_station="BAR")
        result = self.confirm({"product_id": str(simple.id), "quantity": 3}, key="water")
        assert result.status_code == 201 and result.json()["items"][0]["line_total_cents"] == 1503
