"""PostgreSQL-backed two-person close corrections: money stays immutable until approval."""
from datetime import date, timedelta
from unittest import skipUnless

from django.db import DatabaseError, connection, transaction
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from modules.access.context import ActorContext
from modules.access.models import StaffMember, StaffSession, VenueStaffMembership
from modules.cash.models import CashCorrectionRequest, CashMovement, CashPoint
from modules.cash.correction_approval import (
    CashCorrectionError, correction_payload, request_cash_correction, decide_cash_correction,
)
from modules.cash.correction_views import (
    CashCorrectionShiftView, CashCorrectionDecisionView, CashCorrectionManagementView,
)
from modules.cash.daily_close import DailyCloseError, generate_daily_close, review_daily_close
from modules.cash.daily_close_views import close_payload
from modules.cash.services import open_cash_shift, start_cash_count, close_cash_shift
from modules.cash.views import CashLateCorrectionView
from modules.venue.models import Venue


class CashCorrectionApprovalTests(TransactionTestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Cash approval", slug="cash-approval", timezone="America/Sao_Paulo")
        self.cashier, self.cashier_actor = self.operator("CASHIER", "cash-approver-cashier")
        self.manager, self.manager_actor = self.operator("MANAGER", "cash-approver-manager")
        self.second_manager, self.second_actor = self.operator("MANAGER", "cash-approver-other")
        self.day = date(2026, 1, 2)
        self.point = CashPoint.objects.create(venue=self.venue, label="Till")
        shift = open_cash_shift(cash_point_id=self.point.pk, opening_float_cents=5000,
            business_date=self.day, idempotency_key="open", actor=self.cashier_actor)
        counting = start_cash_count(shift_id=shift.pk, actor=self.cashier_actor)
        self.shift = close_cash_shift(shift_id=shift.pk, counted_amount_cents=5000,
            review_threshold_cents=0, expected_version=counting.version, actor=self.cashier_actor)

    def operator(self, role, identifier, venue=None, fresh=True):
        venue = venue or self.venue
        staff = StaffMember.objects.create(display_name=identifier, login_identifier=identifier)
        member = VenueStaffMembership.objects.create(venue=venue, staff_member=staff, role=role)
        session = StaffSession.objects.create(venue=venue, staff_member=staff, membership=member,
            access_expires_at=timezone.now() + timedelta(minutes=15),
            expires_at=timezone.now() + timedelta(hours=1),
            recently_reauthenticated_at=timezone.now() if fresh else None)
        return staff, ActorContext.from_session(session)

    def request(self, view, actor, method="post", data=None, **kwargs):
        factory = APIRequestFactory()
        request = getattr(factory, method)("/", data or {}, format="json")
        session = StaffSession.objects.get(pk=actor.session_id)
        request.actor_context = ActorContext.from_session(session)
        force_authenticate(request, user=session.staff_member, token=session)
        return view.as_view()(request, **kwargs)

    def propose(self, key="a", actor=None, amount=-125, reason="Drawer adjustment"):
        return request_cash_correction(
            shift_id=self.shift.id, amount_cents=amount, reason=reason,
            idempotency_key=key, actor=actor or self.cashier_actor)

    def test_proposal_has_no_money_effect_and_two_person_approval_is_idempotent(self):
        baseline = generate_daily_close(day=self.day, idempotency_key="baseline", actor=self.manager_actor)
        self.assertEqual(baseline.status, "READY_FOR_REVIEW")
        review_daily_close(close_id=baseline.pk, expected_version=1, reason="Original approved", actor=self.manager_actor)
        original = baseline.snapshot
        row, created = self.propose()
        self.assertTrue(created)
        self.assertEqual(row.status, "PENDING")
        self.assertEqual(CashMovement.objects.filter(kind="CORRECTION").count(), 0)
        self.assertEqual(self.propose()[0].id, row.pk)
        with self.assertRaises(CashCorrectionError) as mismatch:
            self.propose(amount=-100)
        self.assertEqual(mismatch.exception.code, "IDEMPOTENCY_CONFLICT")
        incomplete = generate_daily_close(day=self.day, idempotency_key="pending", actor=self.manager_actor)
        self.assertEqual(incomplete.status, "INCOMPLETE")
        self.assertIn("PENDING_CASH_CORRECTION", [r["kind"] for r in incomplete.snapshot["blockers"]])
        with self.assertRaises(DailyCloseError):
            review_daily_close(close_id=incomplete.pk, expected_version=1, reason="Cannot review", actor=self.manager_actor)
        with self.assertRaises(CashCorrectionError) as self_approval:
            decide_cash_correction(request_id=row.pk, expected_version=1, decision="APPROVED",
                reason="Not independent", actor=self.cashier_actor)
        self.assertEqual(self_approval.exception.code, "SELF_APPROVAL_FORBIDDEN")
        approved = decide_cash_correction(request_id=row.pk, expected_version=1, decision="APPROVED",
            reason="Checked with separate reviewer", actor=self.second_actor)
        self.assertEqual(approved.version, 2)
        self.assertIsNotNone(approved.movement_id)
        self.assertEqual(CashMovement.objects.filter(kind="CORRECTION").count(), 1)
        replay = decide_cash_correction(request_id=row.pk, expected_version=1, decision="APPROVED",
            reason="Checked with separate reviewer", actor=self.second_actor)
        self.assertEqual(replay.movement_id, approved.movement_id)
        self.assertEqual(CashMovement.objects.filter(kind="CORRECTION").count(), 1)
        with self.assertRaises(CashCorrectionError):
            decide_cash_correction(request_id=row.pk, expected_version=1, decision="REJECTED",
                reason="Attempt to reverse decision", actor=self.manager_actor)
        old_payload = close_payload(baseline)
        self.assertEqual(old_payload["status"], "REVIEWED")
        self.assertEqual(old_payload["original"], original)
        self.assertEqual(old_payload["corrected_cash_delta_cents"], -125)
        ready = generate_daily_close(day=self.day, idempotency_key="post-decision", actor=self.manager_actor)
        self.assertEqual(ready.status, "READY_FOR_REVIEW")

    def test_rejected_proposal_never_creates_money_and_has_history(self):
        row, _ = self.propose(key="reject")
        rejected = decide_cash_correction(request_id=row.id, expected_version=1,
            decision="REJECTED", reason="Insufficient evidence", actor=self.manager_actor)
        self.assertEqual(rejected.status, "REJECTED")
        self.assertIsNone(rejected.movement_id)
        self.assertEqual(CashMovement.objects.filter(kind="CORRECTION").count(), 0)
        self.assertEqual(correction_payload(rejected)["decision_reason"], "Insufficient evidence")

    def test_permissions_recent_pin_tenant_isolation_and_legacy_bypass(self):
        response = self.request(CashCorrectionShiftView, self.cashier_actor,
            data={"amount_cents": -100, "reason": "Receipt mismatch", "idempotency_key": "http"},
            shift_id=self.shift.pk)
        self.assertEqual(response.status_code, 201)
        row_id = response.data["id"]
        self.assertEqual(self.request(CashCorrectionShiftView, self.cashier_actor,
            data={"amount_cents": -100, "reason": "Receipt mismatch", "idempotency_key": "http"},
            shift_id=self.shift.pk).status_code, 200)
        data = {"expected_version": 1, "decision": "APPROVED", "reason": "Checked evidence"}
        denied = self.request(CashCorrectionDecisionView, self.cashier_actor, data=data, request_id=row_id)
        self.assertEqual(denied.status_code, 403)
        stale_staff, stale_actor = self.operator("MANAGER", "stale-cash-manager", fresh=False)
        missing_pin = self.request(CashCorrectionDecisionView, stale_actor, data=data, request_id=row_id)
        self.assertEqual(missing_pin.status_code, 403)
        self.assertEqual(missing_pin.data["code"], "REAUTH_REQUIRED")
        self_requested = self.request(CashCorrectionDecisionView, self.cashier_actor, data=data, request_id=row_id)
        self.assertEqual(self_requested.status_code, 403)
        approved = self.request(CashCorrectionDecisionView, self.manager_actor, data=data, request_id=row_id)
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.data["status"], "APPROVED")
        hidden_venue = Venue.objects.create(name="Other", slug="cash-approval-other")
        _, hidden_actor = self.operator("MANAGER", "other-venue-manager", venue=hidden_venue)
        self.assertEqual(self.request(CashCorrectionDecisionView, hidden_actor, data=data, request_id=row_id).status_code, 404)
        self.assertEqual(self.request(CashCorrectionManagementView, hidden_actor, method="get",
            data={"business_date": self.day.isoformat()}).data["results"], [])
        blocked = self.request(CashLateCorrectionView, self.manager_actor,
            data={"amount_cents": 5, "reason": "Bypass", "idempotency_key": "legacy"}, shift_id=self.shift.pk)
        self.assertEqual(blocked.status_code, 409)
        self.assertEqual(blocked.data["code"], "CASH_CORRECTION_APPROVAL_REQUIRED")

    @skipUnless(connection.vendor == "postgresql", "Immutable decision trigger requires PostgreSQL")
    def test_reviewed_correction_is_database_immutable(self):
        row, _ = self.propose()
        decide_cash_correction(request_id=row.pk, expected_version=1, decision="REJECTED",
            reason="Wrong proof", actor=self.manager_actor)
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                CashCorrectionRequest.objects.filter(pk=row.pk).update(status="APPROVED", version=3)
        row.refresh_from_db()
        self.assertEqual(row.status, "REJECTED")
