from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.access.context import ActorContext
from modules.access.models import StaffMember, StaffRole, StaffSession, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.catalog.models import FulfillmentStation, Product
from modules.corrections.models import (
    CorrectionKind,
    CorrectionStatus,
    FinancialDisposition,
    OrderCorrection,
    WasteKind,
    WasteMarker,
)
from modules.corrections.services import CorrectionServiceError, cancel_before_fulfillment
from modules.ledger.models import Payment, PaymentMethod, PaymentStatus
from modules.ordering.models import Order, OrderItem, OrderItemState, OrderSource, Tab
from modules.venue.models import Venue


class CorrectionFoundationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.venue = Venue.objects.create(name="Correções", slug="corrections-bar")
        self.other_venue = Venue.objects.create(name="Outro", slug="corrections-other")
        self.staff = StaffMember.objects.create(
            display_name="Ana", login_identifier="corrections-ana"
        )
        self.staff.set_pin("1234")
        self.staff.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(
            venue=self.venue, staff_member=self.staff, role=StaffRole.STAFF
        )
        login = self.client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": self.staff.login_identifier,
                "pin": "1234",
                "installation_id": "corrections-device",
                "platform": "WEB",
            },
            format="json",
        )
        assert login.status_code == 200, login.json()
        self.actor = ActorContext.from_session(StaffSession.objects.get(venue=self.venue))

    def item(self, *, state=OrderItemState.ACCEPTED, venue=None, tab=None, name="Cerveja"):
        venue = venue or self.venue
        tab = tab or Tab.objects.create(venue=venue, display_label="Ana")
        product = Product.objects.create(
            venue=venue,
            name=name,
            price_cents=1200,
            fulfillment_station=FulfillmentStation.BAR,
        )
        order = Order.objects.create(tab=tab, source=OrderSource.STAFF)
        return OrderItem.objects.create(
            order=order,
            product=product,
            product_name_snapshot=product.name,
            unit_price_cents=product.price_cents,
            quantity=1,
            state=state,
            accepted_at=timezone.now() if state == OrderItemState.ACCEPTED else None,
        )

    def cancel(self, item, *, key="cancel-1", reason_code="WRONG_ENTRY", hook=None):
        return cancel_before_fulfillment(
            item_id=item.id,
            kind=CorrectionKind.WRONG_ITEM_ENTERED,
            reason_code=reason_code,
            reason_text="Lançamento duplicado",
            idempotency_key=key,
            actor=self.actor,
            financial_reversal_hook=hook,
        )

    def test_cancel_preserves_snapshot_and_records_append_only_correction_after_reversal_hook(self):
        item = self.item()
        hook_calls = []

        def append_real_reversal(correction, hooked_item, actor):
            hook_calls.append((correction.id, hooked_item.id, actor.staff_id))

        correction = self.cancel(item, hook=append_real_reversal)
        item.refresh_from_db()

        assert correction.status == CorrectionStatus.APPLIED
        assert correction.stage_at_request == OrderItemState.ACCEPTED
        assert correction.kind == CorrectionKind.WRONG_ITEM_ENTERED
        assert correction.financial_disposition == FinancialDisposition.REVERSE_OPEN_RESPONSIBILITY
        assert correction.requested_by_id == self.staff.id
        assert correction.approved_by_id == self.staff.id
        assert correction.applied_at is not None
        assert hook_calls == [(correction.id, item.id, self.staff.id)]
        assert item.state == OrderItemState.CANCELLED
        assert item.cancelled_at is not None
        assert item.product_name_snapshot == "Cerveja"
        assert item.unit_price_cents == 1200
        assert AuditEvent.objects.filter(
            event_type="order_item.cancelled", entity_id=str(correction.id), reason="WRONG_ENTRY"
        ).exists()

    def test_same_idempotency_key_replays_without_second_reversal_or_correction(self):
        item = self.item()
        hook_calls = []

        def hook(*args):
            hook_calls.append(args[0].id)

        first = self.cancel(item, key="replay-cancel", hook=hook)
        replay = self.cancel(item, key="replay-cancel", hook=hook)

        assert replay.id == first.id
        assert replay._idempotency_replay is True
        assert hook_calls == [first.id]
        assert OrderCorrection.objects.filter(original_order_item=item).count() == 1
        assert AuditEvent.objects.filter(event_type="order_item.cancelled").count() == 1

    def test_same_idempotency_key_with_different_intent_is_rejected(self):
        item = self.item()
        self.cancel(item, key="fixed-key", hook=lambda *_: None)

        with self.assertRaises(CorrectionServiceError) as captured:
            self.cancel(item, key="fixed-key", reason_code="CUSTOMER_LEFT", hook=lambda *_: None)

        assert captured.exception.code == "IDEMPOTENCY_CONFLICT"

    def test_no_canonical_cancellation_occurs_without_ledger_reversal_hook(self):
        item = self.item()

        with self.assertRaises(CorrectionServiceError) as captured:
            self.cancel(item, hook=None)

        assert captured.exception.code == "FINANCIAL_REVERSAL_INTEGRATION_REQUIRED"
        item.refresh_from_db()
        assert item.state == OrderItemState.ACCEPTED
        assert not OrderCorrection.objects.filter(original_order_item=item).exists()

    def test_failed_reversal_rolls_back_correction_and_operational_cancellation(self):
        item = self.item()

        def failed_reversal(*args):
            raise RuntimeError("ledger unavailable")

        with self.assertRaises(RuntimeError):
            self.cancel(item, hook=failed_reversal)

        item.refresh_from_db()
        assert item.state == OrderItemState.ACCEPTED
        assert not OrderCorrection.objects.filter(original_order_item=item).exists()
        assert not AuditEvent.objects.filter(event_type="order_item.cancelled").exists()

    def test_preparing_item_requires_later_manager_correction_path(self):
        item = self.item(state=OrderItemState.PREPARING)

        with self.assertRaises(CorrectionServiceError) as captured:
            self.cancel(item, hook=lambda *_: None)

        assert captured.exception.code == "CORRECTION_STAGE_REQUIRES_APPROVAL"
        item.refresh_from_db()
        assert item.state == OrderItemState.PREPARING

    def test_confirmed_money_requires_refund_or_courtesy_orchestration(self):
        item = self.item()
        Payment.objects.create(
            tab=item.order.tab,
            amount_cents=1200,
            method=PaymentMethod.CASH,
            idempotency_key="paid-correction",
            status=PaymentStatus.CONFIRMED,
            confirmed_at=timezone.now(),
            received_by=self.staff,
        )

        with self.assertRaises(CorrectionServiceError) as captured:
            self.cancel(item, hook=lambda *_: self.fail("hook must not run"))

        assert captured.exception.code == "PAID_CORRECTION_REQUIRES_REFUND"
        item.refresh_from_db()
        assert item.state == OrderItemState.ACCEPTED

    def test_other_venue_cannot_cancel_item(self):
        other_item = self.item(venue=self.other_venue)

        with self.assertRaises(CorrectionServiceError) as captured:
            self.cancel(other_item, hook=lambda *_: None)

        assert captured.exception.code == "ORDER_ITEM_NOT_FOUND"

    def test_replacement_link_and_waste_marker_are_separate_operational_history(self):
        original = self.item()
        replacement = self.item(tab=original.order.tab, name="Cerveja sem gelo")
        correction = OrderCorrection.objects.create(
            venue=self.venue,
            original_order_item=original,
            replacement_order_item=replacement,
            kind=CorrectionKind.REPLACEMENT,
            stage_at_request=original.state,
            status=CorrectionStatus.APPLIED,
            reason_code="WRONG_ITEM",
            financial_disposition=FinancialDisposition.MANUAL_REVIEW_REQUIRED,
            idempotency_key="replacement-link",
            request_fingerprint="a" * 64,
            requested_by=self.staff,
            approved_by=self.staff,
            applied_at=timezone.now(),
        )
        waste = WasteMarker.objects.create(
            venue=self.venue,
            order_item=original,
            correction=correction,
            kind=WasteKind.PREPARED_NOT_SERVED,
            quantity=1,
            reason="Item incorreto descartado",
            created_by=self.staff,
            occurred_at=timezone.now() - timedelta(minutes=1),
        )

        assert correction.original_order_item_id == original.id
        assert correction.replacement_order_item_id == replacement.id
        assert waste.correction_id == correction.id
        assert original.product_name_snapshot == "Cerveja"
