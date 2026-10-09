from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from modules.access.models import StaffMember
from modules.catalog.models import (
    ModifierGroup,
    ModifierOption,
    Product,
    ProductModifierGroup,
    ProductVariant,
)
from modules.corrections.models import OrderCorrection
from modules.ledger.models import Charge
from modules.ordering.customization_mix import selection_mix
from modules.ordering.models import Order, OrderItem, Tab
from modules.ordering.services import confirm_order
from modules.venue.models import Venue


class CustomizationMixTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Mix", slug="mix-test")
        self.product = Product.objects.create(
            venue=self.venue, name="Burger", price_cents=3000, fulfillment_station="KITCHEN"
        )
        self.variant = ProductVariant.objects.create(
            product=self.product, name="Large", price_cents=3500
        )
        self.group = ModifierGroup.objects.create(
            venue=self.venue, name="Extras", selection_mode="MULTI", max_selections=2
        )
        ProductModifierGroup.objects.create(product=self.product, group=self.group)
        self.extra = ModifierOption.objects.create(
            group=self.group, name="Cheese", price_delta_cents=300, semantic_kind="ADD"
        )
        self.removal = ModifierOption.objects.create(
            group=self.group, name="No onion", semantic_kind="REMOVE"
        )
        self.tab = Tab.objects.create(venue=self.venue, operating_limit_cents=100000)
        self.start = timezone.now() - timedelta(hours=1)
        self.end = timezone.now() + timedelta(hours=1)

    def confirm(self, key="mix", quantity=2):
        return confirm_order(
            tab_id=self.tab.pk,
            source="STAFF",
            idempotency_key=key,
            lines=[
                {
                    "product_id": self.product.pk,
                    "quantity": quantity,
                    "variant_id": self.variant.pk,
                    "modifier_option_ids": [self.extra.pk, self.removal.pk],
                }
            ],
        )

    def mix(self, **overrides):
        return selection_mix(
            **{"venue_id": self.venue.pk, "start": self.start, "end": self.end, **overrides}
        )

    def test_quantity_cents_zero_removal_and_replay_read_only(self):
        order = self.confirm()
        assert self.confirm().pk == order.pk
        assert order.items.get().unit_price_cents == 3800
        before = (Order.objects.count(), OrderItem.objects.count(), Charge.objects.count())
        result = self.mix()
        assert result == self.mix()
        assert result["basis"] == "GROSS_CONFIRMED_SELECTIONS"
        assert result["products"][0]["confirmed_units"] == 2
        assert result["products"][0]["modifier_attached_units"] == 2
        assert result["variants"][0]["selected_units"] == 2
        assert result["variants"][0]["base_total_cents"] == 7000
        rows = {row["option_name"]: row for row in result["modifiers"]}
        assert rows["Cheese"]["delta_total_cents"] == 600
        assert rows["No onion"]["delta_total_cents"] == 0
        assert all(row["product_units"] == row["selected_units"] == 2 for row in rows.values())
        assert before == (Order.objects.count(), OrderItem.objects.count(), Charge.objects.count())

    def test_historical_price_label_revisions_and_deleted_catalog_choices(self):
        self.confirm()
        self.extra.name = "New cheese"
        self.extra.price_delta_cents = 900
        self.extra.save()
        self.variant.name = "New large"
        self.variant.price_cents = 4000
        self.variant.save()
        self.confirm(key="edited", quantity=1)
        self.variant.delete()
        self.extra.delete()
        self.group.delete()
        self.product.name = "New burger"
        self.product.price_cents = 9999
        self.product.save()
        result = self.mix()
        assert {
            (row["variant_name"], row["base_price_cents"], row["selected_units"])
            for row in result["variants"]
        } == {("Large", 3500, 2), ("New large", 4000, 1)}
        rows = {row["option_name"]: row for row in result["modifiers"]}
        assert rows["Cheese"]["delta_total_cents"] == 600
        assert rows["New cheese"]["delta_total_cents"] == 900
        assert all(row["product_name"] == "Burger" for row in result["variants"])

    def test_venue_and_half_open_interval_isolation(self):
        order = self.confirm()
        assert self.mix(end=order.confirmed_at)["products"] == []
        assert self.mix(start=order.confirmed_at)["products"][0]["confirmed_units"] == 2
        other = Venue.objects.create(name="Other", slug="mix-other")
        assert self.mix(venue_id=other.pk)["products"] == []
        for start, end in ((self.start.replace(tzinfo=None), self.end), (self.end, self.start)):
            with self.assertRaises(ValueError):
                self.mix(start=start, end=end)

    def test_legacy_simple_snapshot_and_attach_denominator(self):
        self.confirm()
        order = Order.objects.create(tab=self.tab, source="STAFF")
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name_snapshot="Burger",
            unit_price_cents=2500,
            quantity=3,
        )
        result = self.mix()
        assert result["products"][0]["confirmed_units"] == 5
        assert result["products"][0]["customized_units"] == 2
        assert all(row["product_units"] == 5 for row in result["modifiers"])
        legacy = next(row for row in result["variants"] if row["variant_id"] is None)
        assert legacy["base_total_cents"] == 7500 and legacy["selected_units"] == 3

    def test_cancelled_original_is_explicit_and_correction_child_is_not_a_sale(self):
        order = self.confirm()
        original = order.items.get()
        original.state = "CANCELLED"
        original.save(update_fields=["state"])
        child = OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name_snapshot="Burger",
            unit_price_cents=3800,
            quantity=2,
            customization_snapshot=original.customization_snapshot,
        )
        actor = StaffMember.objects.create(display_name="Manager", login_identifier="mix-manager")
        OrderCorrection.objects.create(
            venue=self.venue,
            original_order_item=original,
            replacement_order_item=child,
            kind="REMAKE",
            stage_at_request="PREPARING",
            status="APPLIED",
            reason_code="STATION_MISTAKE",
            requested_by=actor,
            idempotency_key="remake",
        )
        result = self.mix()
        assert result["products"][0]["confirmed_units"] == 2
        assert result["products"][0]["cancelled_units"] == 2
        assert all(
            row["selected_units"] == row["cancelled_units"] == 2 for row in result["modifiers"]
        )
