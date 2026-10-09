from types import SimpleNamespace

from django.db import transaction
from django.test import TestCase
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffSession, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.catalog.models import (
    ModifierGroup,
    ModifierOption,
    Product,
    ProductModifierGroup,
    ProductVariant,
)
from modules.realtime.models import OutboxEvent
from modules.realtime.views import visible
from modules.venue.models import Venue


class CustomizationEventTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Events", slug="choice-events")
        staff = StaffMember.objects.create(display_name="Manager", login_identifier="choice-events")
        staff.set_pin("2468")
        staff.save()
        VenueStaffMembership.objects.create(venue=self.venue, staff_member=staff, role="MANAGER")
        self.client = APIClient()
        login = self.client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": staff.login_identifier,
                "pin": "2468",
                "installation_id": "choice-events",
                "platform": "WEB",
            },
            format="json",
        ).json()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login["access_token"])
        self.session = StaffSession.objects.get(pk=login["session_id"])
        self.product = Product.objects.create(
            venue=self.venue, name="Burger", price_cents=1000, fulfillment_station="KITCHEN"
        )
        self.other = Product.objects.create(
            venue=self.venue, name="Sandwich", price_cents=1000, fulfillment_station="BAR"
        )
        self.group = ModifierGroup.objects.create(
            venue=self.venue, name="Extras", selection_mode="MULTI"
        )
        for product in (self.product, self.other):
            ProductModifierGroup.objects.create(product=product, group=self.group)
        self.option = ModifierOption.objects.create(group=self.group, name="Cheese")

    def change(self, kind, choice):
        return self.client.post(
            f"/catalog/products/{self.product.pk}/customization/{kind}/{choice.pk}/availability/",
            {"state": "UNAVAILABLE", "expected_version": 1, "reason": "Sold out"},
            format="json",
        )

    def test_shared_option_emits_for_every_affected_product_and_is_visible_to_guest_staff(self):
        assert self.change("option", self.option).status_code == 200
        events = list(OutboxEvent.objects.filter(event_type="catalog.option_availability_changed"))
        assert {event.aggregate_id for event in events} == {
            str(self.product.pk),
            str(self.other.pk),
        }
        for event in events:
            assert event.aggregate_type == "Product"
            assert visible(event, self.session, False)
            assert visible(event, SimpleNamespace(tab_id=None), True)
            # The shared bridge deliberately sends invalidation only; clients
            # reload canonical Catalog. Audit details never become public payloads.
            assert event.payload == {}
        audit = AuditEvent.objects.get(event_type="catalog.option_availability_changed")
        assert (
            audit.actor_session_id == self.session.pk and audit.device_id == self.session.device_id
        )
        assert audit.metadata["before"] == "AVAILABLE" and audit.metadata["after"] == "UNAVAILABLE"
        assert audit.metadata["reason"] == "Sold out"
        assert self.change("option", self.option).status_code == 409
        assert (
            OutboxEvent.objects.filter(event_type="catalog.option_availability_changed").count()
            == 2
        )

    def test_variant_event_and_availability_roll_back_together(self):
        variant = ProductVariant.objects.create(
            product=self.product, name="Large", price_cents=1500
        )
        with transaction.atomic():
            assert self.change("variant", variant).status_code == 200
            assert (
                OutboxEvent.objects.filter(
                    event_type="catalog.variant_availability_changed"
                ).count()
                == 1
            )
            transaction.set_rollback(True)
        variant.refresh_from_db()
        assert variant.availability == "AVAILABLE" and variant.version == 1
        assert not OutboxEvent.objects.filter(
            event_type="catalog.variant_availability_changed"
        ).exists()
        assert not AuditEvent.objects.filter(
            event_type="catalog.variant_availability_changed"
        ).exists()
