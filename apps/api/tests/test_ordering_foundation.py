from django.test import TestCase
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.catalog.models import AvailabilityState, FulfillmentStation, Product
from modules.ordering.models import OrderItem, OrderSource, Tab, TabState
from modules.ordering.services import OrderingServiceError, confirm_order
from modules.venue.models import Venue


class OrderingFoundationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.venue = Venue.objects.create(name="Bar", slug="ordering-bar")
        self.other_venue = Venue.objects.create(name="Outro", slug="ordering-other")
        self.staff = StaffMember.objects.create(
            display_name="Ana",
            login_identifier="ordering-ana",
        )
        self.staff.set_pin("1234")
        self.staff.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(
            venue=self.venue,
            staff_member=self.staff,
            role=StaffRole.STAFF,
        )
        login = self.client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": self.staff.login_identifier,
                "pin": "1234",
                "installation_id": "ordering-device",
                "platform": "WEB",
            },
            format="json",
        )
        assert login.status_code == 200, login.json()
        self.access_token = login.json()["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)

    def product(
        self,
        *,
        venue=None,
        name="Cerveja",
        price_cents=1200,
        active=True,
    ):
        return Product.objects.create(
            venue=venue or self.venue,
            name=name,
            price_cents=price_cents,
            active=active,
            fulfillment_station=FulfillmentStation.BAR,
        )

    def open_tab(self, label=""):
        response = self.client.post(
            "/tabs/",
            {"display_label": label},
            format="json",
        )
        assert response.status_code == 201, response.json()
        return response.json()

    def test_staff_opens_tab_without_table_customer_or_label(self):
        payload = self.open_tab()

        tab = Tab.objects.get(pk=payload["id"])
        assert tab.display_label == ""
        assert tab.state == TabState.OPEN
        assert tab.version == 1
        assert tab.venue_id == self.venue.id
        assert tab.opened_by_id == self.staff.id

        event = AuditEvent.objects.get(
            venue=self.venue,
            event_type="tab.opened",
            entity_id=str(tab.id),
        )
        assert event.actor_staff_id == self.staff.id
        assert event.actor_session_id is not None
        assert event.device_id is not None

    def test_tab_can_have_simple_display_label(self):
        payload = self.open_tab("Mesa da rua / Lucas")

        assert payload["display_label"] == "Mesa da rua / Lucas"

    def test_available_product_confirms_order_with_price_snapshot(self):
        tab = self.open_tab("Comanda 1")
        product = self.product(price_cents=1350)

        response = self.client.post(
            f"/tabs/{tab['id']}/orders/confirm/",
            {
                "lines": [
                    {"product_id": str(product.id), "quantity": 2},
                ]
            },
            format="json",
        )

        assert response.status_code == 201, response.json()
        body = response.json()
        assert body["tab_id"] == tab["id"]
        assert body["source"] == OrderSource.STAFF
        assert body["items"][0]["unit_price_cents"] == 1350
        assert body["items"][0]["quantity"] == 2
        assert body["items"][0]["line_total_cents"] == 2700

        product.price_cents = 1500
        product.name = "Cerveja nova"
        product.save()

        item = OrderItem.objects.get(pk=body["items"][0]["id"])
        assert item.unit_price_cents == 1350
        assert item.product_name_snapshot == "Cerveja"

        saved_tab = Tab.objects.get(pk=tab["id"])
        assert saved_tab.version == 2

    def test_unavailable_product_blocks_whole_order(self):
        tab = self.open_tab()
        available = self.product(name="Água", price_cents=500)
        unavailable = self.product(name="Batata", price_cents=2800)
        unavailable.availability.state = AvailabilityState.UNAVAILABLE
        unavailable.availability.version += 1
        unavailable.availability.save(
            update_fields=["state", "version", "changed_at"],
        )

        response = self.client.post(
            f"/tabs/{tab['id']}/orders/confirm/",
            {
                "lines": [
                    {"product_id": str(available.id), "quantity": 1},
                    {"product_id": str(unavailable.id), "quantity": 1},
                ]
            },
            format="json",
        )

        assert response.status_code == 409
        assert response.json()["code"] == "PRODUCTS_NOT_CONFIRMABLE"
        assert response.json()["products"] == [
            {"product_id": str(unavailable.id), "reason": "UNAVAILABLE"}
        ]
        assert OrderItem.objects.count() == 0
        assert Tab.objects.get(pk=tab["id"]).orders.count() == 0

    def test_inactive_product_is_not_confirmable(self):
        tab = self.open_tab()
        product = self.product(active=False)

        response = self.client.post(
            f"/tabs/{tab['id']}/orders/confirm/",
            {
                "lines": [
                    {"product_id": str(product.id), "quantity": 1},
                ]
            },
            format="json",
        )

        assert response.status_code == 409
        assert response.json()["products"][0]["reason"] == "INACTIVE"

    def test_stale_cart_revalidates_at_confirmation_time(self):
        tab = self.open_tab()
        product = self.product(name="Última porção")

        # Cart was assembled while available. The canonical state changes
        # before confirmation.
        product.availability.state = AvailabilityState.UNAVAILABLE
        product.availability.version += 1
        product.availability.save(
            update_fields=["state", "version", "changed_at"],
        )

        response = self.client.post(
            f"/tabs/{tab['id']}/orders/confirm/",
            {
                "lines": [
                    {"product_id": str(product.id), "quantity": 1},
                ]
            },
            format="json",
        )

        assert response.status_code == 409
        assert response.json()["code"] == "PRODUCTS_NOT_CONFIRMABLE"
        assert OrderItem.objects.count() == 0

    def test_post_confirmation_availability_change_does_not_rewrite_item(self):
        tab = self.open_tab()
        product = self.product(name="Coca")

        response = self.client.post(
            f"/tabs/{tab['id']}/orders/confirm/",
            {
                "lines": [
                    {"product_id": str(product.id), "quantity": 1},
                ]
            },
            format="json",
        )
        assert response.status_code == 201
        item_id = response.json()["items"][0]["id"]

        product.availability.state = AvailabilityState.UNAVAILABLE
        product.availability.version += 1
        product.availability.save(
            update_fields=["state", "version", "changed_at"],
        )

        item = OrderItem.objects.get(pk=item_id)
        assert item.state == "NEW"
        assert item.unit_price_cents == product.price_cents
        assert item.product_name_snapshot == product.name

    def test_product_from_other_venue_is_rejected_without_leaking_existence(self):
        tab = self.open_tab()
        product = self.product(venue=self.other_venue, name="Produto externo")

        response = self.client.post(
            f"/tabs/{tab['id']}/orders/confirm/",
            {
                "lines": [
                    {"product_id": str(product.id), "quantity": 1},
                ]
            },
            format="json",
        )

        assert response.status_code == 409
        assert response.json()["products"] == [
            {
                "product_id": str(product.id),
                "reason": "NOT_FOUND_OR_OTHER_VENUE",
            }
        ]

    def test_closed_tab_cannot_receive_order(self):
        tab = Tab.objects.create(
            venue=self.venue,
            display_label="Fechada",
            state=TabState.CLOSED,
        )
        product = self.product()

        response = self.client.post(
            f"/tabs/{tab.id}/orders/confirm/",
            {
                "lines": [
                    {"product_id": str(product.id), "quantity": 1},
                ]
            },
            format="json",
        )

        assert response.status_code == 409
        assert response.json()["code"] == "TAB_NOT_OPEN"

    def test_service_supports_guest_source_without_staff_actor(self):
        tab = Tab.objects.create(venue=self.venue)
        product = self.product(name="Pedido guest")

        order = confirm_order(
            tab_id=tab.id,
            source=OrderSource.GUEST,
            lines=[{"product_id": product.id, "quantity": 1}],
            actor=None,
        )

        assert order.source == OrderSource.GUEST
        assert order.confirmed_by_id is None
        assert order.tab_id == tab.id
