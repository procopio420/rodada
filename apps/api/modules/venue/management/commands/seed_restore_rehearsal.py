"""Persist an idempotent, cross-domain fixture used by backup recovery drills."""

import hashlib
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from modules.access.context import ActorContext
from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.cash.services import (
    close_cash_shift,
    create_cash_point,
    open_cash_shift,
    start_cash_count,
    supply_cash,
    withdraw_cash,
)
from modules.catalog.models import FulfillmentStation, Product
from modules.corrections.services import (
    cancel_before_fulfillment,
    settle_refund_required_cancellation,
)
from modules.dispatch.services import complete_delivery_task
from modules.guest_access.models import GuestSession
from modules.hospitality.models import GuestOrderingMode, Table, TableOccupancy
from modules.hospitality.services import assign_tab, occupy_table
from modules.ledger.models import PaymentMethod
from modules.ledger.services import close_tab, collect_payment, reverse_open_responsibility
from modules.ordering.models import OrderItemState, OrderSource
from modules.ordering.services import confirm_order, open_tab, transition_order_item
from modules.venue.models import Venue


class Command(BaseCommand):
    help = "Cria fatos representativos e idempotentes para o ensaio de backup/restore."

    def add_arguments(self, parser):
        parser.add_argument("--venue-slug", default="restore-rehearsal")

    @transaction.atomic
    def handle(self, *args, **options):
        slug = options["venue_slug"]
        venue, created = Venue.objects.get_or_create(
            slug=slug,
            defaults={"name": "Restore rehearsal venue"},
        )
        if not created:
            self.stdout.write(f"Venue {slug} already exists; preserving its immutable rehearsal history.")

        manager, _ = StaffMember.objects.get_or_create(
            login_identifier=f"{slug}-manager",
            defaults={"display_name": "Restore Manager"},
        )
        if not manager.pin_hash:
            manager.set_pin("0420")
            manager.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.get_or_create(
            venue=venue,
            staff_member=manager,
            defaults={"role": StaffRole.MANAGER},
        )
        actor = ActorContext(venue_id=venue.id, staff_id=manager.id, session_id=None, device_id=None)

        bar, _ = Product.objects.get_or_create(
            venue=venue,
            name="Restore Lager",
            defaults={"price_cents": 1200, "fulfillment_station": FulfillmentStation.BAR},
        )
        kitchen, _ = Product.objects.get_or_create(
            venue=venue,
            name="Restore Fritas",
            defaults={"price_cents": 2400, "fulfillment_station": FulfillmentStation.KITCHEN},
        )
        duplicate, _ = Product.objects.get_or_create(
            venue=venue,
            name="Restore Duplicate",
            defaults={"price_cents": 600, "fulfillment_station": FulfillmentStation.KITCHEN},
        )

        table, _ = Table.objects.get_or_create(
            venue=venue,
            label="Restore 24",
            defaults={"guest_ordering_mode": GuestOrderingMode.DIRECT},
        )
        occupancy = TableOccupancy.objects.filter(table=table, released_at__isnull=True).first()
        if occupancy is None:
            occupancy = occupy_table(table_id=table.id, actor=actor)

        from modules.ordering.models import Tab

        existing_tab = Tab.objects.filter(venue=venue, display_label="Restore history").first()
        if existing_tab is not None:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Rehearsal data already exists: venue={venue.slug} tab={existing_tab.id}"
                )
            )
            return

        from modules.house_account.models import Customer, Relationship
        customer = Customer.objects.create(display_name="Restore customer")
        Relationship.objects.create(venue=venue, customer=customer, kind="HOUSE")
        tab = open_tab(actor=actor, display_label="Restore history", customer_id=customer.id)
        assign_tab(occupancy_id=occupancy.id, tab_id=tab.id, actor=actor)
        order = confirm_order(
            tab_id=tab.id,
            source=OrderSource.STAFF,
            actor=actor,
            idempotency_key="restore-history-order",
            lines=[
                {"product_id": bar.id, "quantity": 1},
                {"product_id": kitchen.id, "quantity": 1},
                {"product_id": duplicate.id, "quantity": 1},
            ],
        )
        # Timestamps can tie in a bulk insert; identify fixture items by Product.
        items = {item.product_id: item for item in order.items.all()}
        for state in (OrderItemState.ACCEPTED, OrderItemState.READY):
            transition_order_item(item_id=items[bar.id].id, target_state=state, actor=actor)
        complete_delivery_task(task_id=items[bar.id].delivery_task.id, actor=actor)
        cancelled = cancel_before_fulfillment(
            item_id=items[duplicate.id].id,
            kind="WRONG_ITEM_ENTERED",
            reason_code="DUPLICATE_ENTRY",
            reason_text="Backup rehearsal duplicate item",
            idempotency_key="restore-unpaid-cancellation",
            actor=actor,
            financial_reversal_hook=reverse_open_responsibility,
        )

        cash_point = create_cash_point(label="Restore drawer", actor=actor)
        shift = open_cash_shift(
            cash_point_id=cash_point.id,
            opening_float_cents=10_000,
            business_date=timezone.localdate(),
            idempotency_key="restore-shift-open",
            actor=actor,
        )
        _cash_payment, _ = collect_payment(
            tab_id=tab.id,
            amount_cents=1200,
            method=PaymentMethod.CASH,
            cash_point_id=cash_point.id,
            amount_tendered_cents=1200,
            idempotency_key="restore-cash-payment",
            actor=actor,
        )
        card_payment, _ = collect_payment(
            tab_id=tab.id,
            amount_cents=2400,
            method=PaymentMethod.CARD,
            idempotency_key="restore-card-payment",
            actor=actor,
        )
        paid_correction = cancel_before_fulfillment(
            item_id=items[kitchen.id].id,
            kind="CUSTOMER_CHANGED_MIND",
            reason_code="CUSTOMER_LEFT",
            reason_text="Backup rehearsal paid correction",
            idempotency_key="restore-paid-cancellation",
            actor=actor,
            financial_reversal_hook=None,
            record_paid_request=True,
        )
        settled, refund, _ = settle_refund_required_cancellation(
            correction_id=paid_correction.id,
            payment_id=card_payment.id,
            amount_cents=2400,
            refund_idempotency_key="restore-card-refund",
            cash_point_id=None,
            actor=actor,
        )
        close_tab(tab_id=tab.id, actor=actor)
        supply_cash(
            shift_id=shift.id,
            amount_cents=300,
            reason="Change float supply",
            idempotency_key="restore-supply",
            actor=actor,
        )
        withdraw_cash(
            shift_id=shift.id,
            amount_cents=500,
            reason="Safe drop",
            idempotency_key="restore-withdrawal",
            actor=actor,
        )
        counting = start_cash_count(shift_id=shift.id, actor=actor)
        closed = close_cash_shift(
            shift_id=shift.id,
            counted_amount_cents=11_000,
            review_threshold_cents=0,
            expected_version=counting.version,
            actor=actor,
        )

        open_point = create_cash_point(label="Restore open drawer", actor=actor)
        open_cash_shift(
            cash_point_id=open_point.id,
            opening_float_cents=500,
            business_date=timezone.localdate(),
            idempotency_key="restore-open-shift",
            actor=actor,
        )
        GuestSession.objects.get_or_create(
            table=table,
            occupancy=occupancy,
            tab=tab,
            generation=occupancy.generation,
            token_digest=hashlib.sha256(b"restore-rehearsal-guest").hexdigest(),
            defaults={"expires_at": timezone.now() + timedelta(days=1)},
        )

        if settled.refund_id != refund.id or cancelled.financial_adjustment_id is None:
            raise CommandError("Restore rehearsal fixture did not retain correction linkage.")
        self.stdout.write(
            self.style.SUCCESS(
                "Rehearsal data created: "
                f"venue={venue.slug} tab={tab.id} closed_shift={closed.id} refund={refund.id}"
            )
        )
