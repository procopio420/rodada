from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from modules.access.context import ActorContext
from modules.access.models import (
    DeviceRegistration,
    StaffMember,
    StaffSession,
    StaffRole,
    VenueStaffMembership,
)
from modules.audit.models import AuditEvent
from modules.cash.models import CashMovement, CashMovementKind, CashReviewStatus, CashShiftStatus, CashTenderDetail
from modules.cash.services import (
    CashServiceError,
    cash_shift_position,
    close_cash_shift,
    create_cash_point,
    open_cash_shift,
    record_cash_payment_movement,
    record_cash_refund_movement,
    record_late_cash_correction,
    review_cash_discrepancy,
    start_cash_count,
    supply_cash,
    withdraw_cash,
)
from modules.ledger.models import Payment, PaymentMethod, PaymentStatus, Refund, RefundStatus
from modules.ordering.models import Tab
from modules.venue.models import Venue


class CashManagementTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Cash venue", slug="cash-venue")
        self.staff = StaffMember.objects.create(display_name="Caixa", login_identifier="cashier")
        membership = VenueStaffMembership.objects.create(
            venue=self.venue, staff_member=self.staff, role=StaffRole.CASHIER
        )
        device = DeviceRegistration.objects.create(
            venue=self.venue, installation_key_hash="cash-test-device", platform="WEB"
        )
        session = StaffSession.objects.create(
            venue=self.venue,
            staff_member=self.staff,
            membership=membership,
            device=device,
            expires_at=timezone.now() + timedelta(hours=8),
        )
        self.actor = ActorContext.from_session(session)
        from modules.cash.models import CashPoint

        self.point = CashPoint.objects.create(venue=self.venue, label="Caixa principal")

    def open_shift(self, *, opening=20_000):
        return open_cash_shift(
            cash_point_id=self.point.id,
            opening_float_cents=opening,
            business_date=timezone.localdate(),
            idempotency_key="open-1",
            actor=self.actor,
        )

    def confirmed_cash_payment(self, *, amount=8_200):
        tab = Tab.objects.create(venue=self.venue, opened_by=self.staff)
        return Payment.objects.create(
            tab=tab,
            amount_cents=amount,
            method=PaymentMethod.CASH,
            idempotency_key=f"payment-{amount}",
            status=PaymentStatus.CONFIRMED,
            confirmed_at=timezone.now(),
            received_by=self.staff,
        )

    def test_opening_float_is_reconstructible_once_and_open_is_idempotent(self):
        shift = self.open_shift()
        replay = self.open_shift()

        self.assertEqual(shift.id, replay.id)
        self.assertEqual(cash_shift_position(shift)["expected_cents"], 20_000)
        self.assertEqual(shift.movements.count(), 1)
        self.assertEqual(shift.movements.get().kind, CashMovementKind.OPENING_FLOAT)

        with self.assertRaises(CashServiceError) as active:
            open_cash_shift(
                cash_point_id=self.point.id,
                opening_float_cents=10_000,
                business_date=timezone.localdate(),
                idempotency_key="open-2",
                actor=self.actor,
            )
        self.assertEqual(active.exception.code, "CASH_SHIFT_ALREADY_ACTIVE")

    def test_supply_and_sangria_are_append_only_and_idempotent(self):
        shift = self.open_shift()
        supply = supply_cash(
            shift_id=shift.id,
            amount_cents=5_000,
            reason="Troco do bar",
            idempotency_key="supply-1",
            actor=self.actor,
        )
        replay = supply_cash(
            shift_id=shift.id,
            amount_cents=5_000,
            reason="Troco do bar",
            idempotency_key="supply-1",
            actor=self.actor,
        )
        withdrawal = withdraw_cash(
            shift_id=shift.id,
            amount_cents=10_000,
            reason="Sangria para cofre",
            idempotency_key="withdraw-1",
            actor=self.actor,
        )

        shift.refresh_from_db()
        self.assertEqual(supply.id, replay.id)
        self.assertEqual(withdrawal.amount_cents, -10_000)
        self.assertEqual(cash_shift_position(shift)["expected_cents"], 15_000)
        self.assertEqual(CashMovement.objects.filter(shift=shift).count(), 3)
        self.assertTrue(AuditEvent.objects.filter(event_type="cash.withdrawn").exists())

    def test_full_drawer_withdrawal_retry_does_not_recheck_depleted_balance(self):
        shift = self.open_shift()
        command = dict(shift_id=shift.id, amount_cents=20_000,
                       reason="Sangria completa", idempotency_key="withdraw-all", actor=self.actor)
        first = withdraw_cash(**command)
        replay = withdraw_cash(**command)
        self.assertEqual(first.id, replay.id)
        self.assertEqual(cash_shift_position(shift)["expected_cents"], 0)
        self.assertEqual(shift.movements.filter(kind=CashMovementKind.WITHDRAWAL).count(), 1)
        with self.assertRaises(CashServiceError) as conflict:
            withdraw_cash(**{**command, "amount_cents": 19_000})
        self.assertEqual(conflict.exception.code, "IDEMPOTENCY_CONFLICT")

    def test_confirmed_cash_payment_records_net_not_tendered_and_refund_once(self):
        shift = self.open_shift()
        payment = self.confirmed_cash_payment()
        movement = record_cash_payment_movement(
            payment_id=payment.id,
            cash_point_id=self.point.id,
            amount_due_cents=8_200,
            amount_tendered_cents=10_000,
            idempotency_key="payment-movement-1",
            actor=self.actor,
        )
        replay = record_cash_payment_movement(
            payment_id=payment.id,
            cash_point_id=self.point.id,
            amount_due_cents=8_200,
            amount_tendered_cents=10_000,
            idempotency_key="payment-movement-1",
            actor=self.actor,
        )
        detail = CashTenderDetail.objects.get(payment=payment)
        self.assertEqual(movement.id, replay.id)
        self.assertEqual(movement.amount_cents, 8_200)
        self.assertEqual(detail.change_given_cents, 1_800)
        shift.refresh_from_db()
        self.assertEqual(cash_shift_position(shift)["expected_cents"], 28_200)

        refund = Refund.objects.create(
            payment=payment,
            amount_cents=1_000,
            idempotency_key="refund-1",
            status=RefundStatus.CONFIRMED,
            confirmed_at=timezone.now(),
            created_by=self.staff,
        )
        refund_movement = record_cash_refund_movement(
            refund_id=refund.id,
            cash_point_id=self.point.id,
            idempotency_key="refund-movement-1",
            actor=self.actor,
        )
        replay_refund = record_cash_refund_movement(
            refund_id=refund.id,
            cash_point_id=self.point.id,
            idempotency_key="refund-movement-1",
            actor=self.actor,
        )
        self.assertEqual(refund_movement.id, replay_refund.id)
        self.assertEqual(refund_movement.amount_cents, -1_000)
        shift.refresh_from_db()
        self.assertEqual(cash_shift_position(shift)["expected_cents"], 27_200)

    def test_count_close_review_and_late_correction_preserve_snapshot(self):
        shift = self.open_shift()
        supply_cash(
            shift_id=shift.id,
            amount_cents=5_000,
            reason="Troco",
            idempotency_key="supply-count",
            actor=self.actor,
        )
        counting = start_cash_count(shift_id=shift.id, actor=self.actor)
        with self.assertRaises(CashServiceError) as blocked:
            supply_cash(
                shift_id=shift.id,
                amount_cents=100,
                reason="depois da contagem",
                idempotency_key="blocked-supply",
                actor=self.actor,
            )
        self.assertEqual(blocked.exception.code, "CASH_SHIFT_COUNTING")

        closed = close_cash_shift(
            shift_id=shift.id,
            counted_amount_cents=24_700,
            review_threshold_cents=100,
            expected_version=counting.version,
            actor=self.actor,
        )
        self.assertEqual(closed.status, CashShiftStatus.CLOSED)
        self.assertEqual(closed.expected_amount_cents_snapshot, 25_000)
        self.assertEqual(closed.discrepancy_cents, -300)
        self.assertEqual(closed.review_status, CashReviewStatus.PENDING)
        with self.assertRaises(CashServiceError) as closed_movement:
            supply_cash(
                shift_id=shift.id,
                amount_cents=100,
                reason="após fechar",
                idempotency_key="closed-supply",
                actor=self.actor,
            )
        self.assertEqual(closed_movement.exception.code, "CASH_SHIFT_CLOSED")
        reviewed = review_cash_discrepancy(
            shift_id=shift.id, reason="Troco contado separadamente", actor=self.actor
        )
        self.assertEqual(reviewed.review_status, CashReviewStatus.REVIEWED)

        correction = record_late_cash_correction(
            shift_id=shift.id,
            amount_cents=-1_000,
            reason="Sangria histórica omitida",
            idempotency_key="late-1",
            actor=self.actor,
        )
        shift.refresh_from_db()
        position = cash_shift_position(shift)
        self.assertTrue(correction.is_post_close_correction)
        self.assertEqual(shift.expected_amount_cents_snapshot, 25_000)
        self.assertEqual(position["post_close_correction_cents"], -1_000)
        self.assertEqual(position["corrected_expected_cents"], 24_000)

    def test_cash_operations_are_venue_scoped(self):
        shift = self.open_shift()
        other_venue = Venue.objects.create(name="Other", slug="other-cash")
        other_staff = StaffMember.objects.create(display_name="Other", login_identifier="other")
        membership = VenueStaffMembership.objects.create(venue=other_venue, staff_member=other_staff)
        other_session = StaffSession.objects.create(
            venue=other_venue,
            staff_member=other_staff,
            membership=membership,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        with self.assertRaises(CashServiceError) as inaccessible:
            supply_cash(
                shift_id=shift.id,
                amount_cents=500,
                reason="cross venue",
                idempotency_key="other-1",
                actor=ActorContext.from_session(other_session),
            )
        self.assertEqual(inaccessible.exception.code, "CASH_SHIFT_NOT_FOUND")

    def test_cash_point_creation_is_venue_scoped_and_audited(self):
        created = create_cash_point(label="Gaveta do bar", actor=self.actor)
        replay = create_cash_point(label="Gaveta do bar", actor=self.actor)
        self.assertEqual(created.id, replay.id)
        self.assertTrue(
            AuditEvent.objects.filter(event_type="cash.point_created", entity_id=str(created.id)).exists()
        )
