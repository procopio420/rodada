from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from threading import Barrier
from unittest import skipUnless
from django.db import connection, close_old_connections, transaction, DatabaseError
from django.test import TransactionTestCase
from django.utils import timezone
from modules.access.context import ActorContext
from modules.access.models import StaffMember, StaffSession, VenueStaffMembership
from modules.cash.models import CashPoint, DailyClose, DailyCloseReview
from modules.cash.services import open_cash_shift, start_cash_count, close_cash_shift, review_cash_discrepancy, record_late_cash_correction, record_cash_payment_movement
from modules.cash.daily_close import generate_daily_close, review_daily_close, DailyCloseError
from modules.cash.daily_close_views import close_payload, DailyCloseDetailView, DailyCloseReviewView, DailyCloseListView
from modules.ledger.models import Payment, Refund
from modules.ordering.models import Tab
from modules.venue.models import Venue
from modules.venue.calendar import business_boundary


class DailyCloseTests(TransactionTestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name='Daily close', slug='daily-close', timezone='America/Sao_Paulo', business_day_cutoff_hour=4)
        self.staff = StaffMember.objects.create(display_name='Manager', login_identifier='daily-manager')
        self.membership = VenueStaffMembership.objects.create(venue=self.venue, staff_member=self.staff, role='MANAGER')
        self.session = StaffSession.objects.create(venue=self.venue, staff_member=self.staff, membership=self.membership,
            access_expires_at=timezone.now()+timedelta(minutes=15),
            expires_at=timezone.now()+timedelta(hours=1), recently_reauthenticated_at=timezone.now())
        self.actor = ActorContext.from_session(self.session)
        self.day = date(2026, 1, 2)
        self.point = CashPoint.objects.create(venue=self.venue, label='Main')

    def generate(self, key='generate-1'):
        return generate_daily_close(day=self.day, idempotency_key=key, actor=self.actor)

    def shift(self, point=None):
        return open_cash_shift(cash_point_id=(point or self.point).pk, opening_float_cents=5000,
            business_date=self.day, idempotency_key='open', actor=self.actor)

    def close(self, shift, count=5000):
        start_cash_count(shift_id=shift.pk, actor=self.actor)
        return close_cash_shift(shift_id=shift.pk, counted_amount_cents=count,
            review_threshold_cents=0, actor=self.actor)

    def test_open_shift_is_incomplete_no_fake_count_and_new_revision_preserves_original(self):
        shift = self.shift()
        original = self.generate()
        self.assertEqual(original.status, 'INCOMPLETE')
        shift.refresh_from_db()
        self.assertIsNone(shift.counted_amount_cents)
        self.assertEqual(self.generate().pk, original.pk)
        with self.assertRaises(DailyCloseError) as error:
            review_daily_close(close_id=original.pk, expected_version=1, reason='review', actor=self.actor)
        self.assertEqual(error.exception.code, 'DAILY_CLOSE_INCOMPLETE')
        self.close(shift)
        revision = self.generate('generate-2')
        self.assertEqual(revision.version, 2)
        self.assertEqual(revision.status, 'READY_FOR_REVIEW')
        original.refresh_from_db()
        self.assertEqual(original.snapshot['cash_shifts'][0]['status'], 'OPEN')

    def test_multiple_drawers_discrepancy_review_and_late_correction_preserve_snapshot(self):
        shift = self.close(self.shift(), 4700)
        other = CashPoint.objects.create(venue=self.venue, label='Bar')
        self.close(self.shift(other))
        blocked = self.generate()
        before = blocked.snapshot
        self.assertEqual(blocked.status, 'INCOMPLETE')
        review_cash_discrepancy(shift_id=shift.pk, reason='Observed shortage', actor=self.actor)
        blocked.refresh_from_db()
        self.assertEqual(blocked.snapshot, before)
        close = self.generate('reviewable')
        review_daily_close(close_id=close.pk, expected_version=close.version, reason='Checked', actor=self.actor)
        self.assertEqual(DailyCloseReview.objects.count(), 1)
        self.assertEqual(len(close.snapshot['cash_shifts']), 2)
        original = close.snapshot
        record_late_cash_correction(shift_id=shift.pk, amount_cents=-1000,
            idempotency_key='late', reason='Omitted withdrawal', actor=self.actor)
        close.refresh_from_db()
        self.assertEqual(close.snapshot, original)
        self.assertEqual(close_payload(close)['corrected_cash_delta_cents'], -1000)
        shift.refresh_from_db()
        self.assertEqual(shift.expected_amount_cents_snapshot, 5000)

    def test_cross_venue_review_not_found_and_stale_snapshot_denied(self):
        close = self.generate()
        other = Venue.objects.create(name='Other', slug='daily-other')
        membership = VenueStaffMembership.objects.create(venue=other, staff_member=self.staff, role='MANAGER')
        session = StaffSession.objects.create(venue=other, staff_member=self.staff, membership=membership,
            access_expires_at=timezone.now()+timedelta(minutes=15),
            expires_at=timezone.now()+timedelta(hours=1), recently_reauthenticated_at=timezone.now())
        actor = ActorContext.from_session(session)
        with self.assertRaises(DailyCloseError) as error:
            review_daily_close(close_id=close.pk, expected_version=1, reason='review', actor=actor)
        self.assertEqual(error.exception.status_code, 404)
        self.shift()
        with self.assertRaises(DailyCloseError) as error:
            review_daily_close(close_id=close.pk, expected_version=1, reason='review', actor=self.actor)
        self.assertEqual(error.exception.code, 'STALE_SNAPSHOT')
        self.assertEqual(DailyCloseReview.objects.count(), 0)

    def test_refund_uses_confirmation_business_date_and_secret_is_not_projected(self):
        tab = Tab.objects.create(venue=self.venue)
        payment = Payment.objects.create(tab=tab, received_by=self.staff, method='PIX', amount_cents=2000,
            idempotency_key='payment', status='CONFIRMED', provider='private-provider-reference',
            confirmed_at=business_boundary(self.venue, self.day)-timedelta(seconds=1))
        Refund.objects.create(payment=payment, created_by=self.staff, amount_cents=500,
            idempotency_key='refund', status='CONFIRMED', confirmed_at=business_boundary(self.venue, self.day)+timedelta(hours=1))
        close = self.generate()
        self.assertEqual(close.snapshot['receipts']['paid_cents'], 0)
        self.assertEqual(close.snapshot['receipts']['refunds_cents'], 500)
        self.assertEqual(close.snapshot['receipts']['net_received_cents'], -500)
        self.assertNotIn('private-provider-reference', str(close.snapshot))

    def request(self, view, *, venue=None, role='MANAGER', fresh=True, close_id=None, data=None, method='post'):
        from rest_framework.test import APIRequestFactory, force_authenticate
        venue = venue or self.venue
        member, _ = VenueStaffMembership.objects.get_or_create(venue=venue, staff_member=self.staff, defaults=dict(role=role))
        member.role = role
        member.save(update_fields=['role'])
        session = StaffSession.objects.create(venue=venue, staff_member=self.staff, membership=member,
            access_expires_at=timezone.now()+timedelta(minutes=15),
            expires_at=timezone.now()+timedelta(hours=1),
            recently_reauthenticated_at=timezone.now() if fresh else None)
        factory = APIRequestFactory()
        request = getattr(factory, method)('/', data or {}, format='json')
        request.actor_context = ActorContext.from_session(session)
        force_authenticate(request, user=self.staff, token=session)
        return view.as_view()(request, **({} if close_id is None else dict(close_id=close_id)))

    def test_api_manager_review_requires_recent_reauth_and_cross_venue_is_hidden(self):
        close = self.generate()
        data = dict(expected_version=close.version, reason='Checked')
        denied = self.request(DailyCloseReviewView, close_id=close.pk, data=data, fresh=False)
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(denied.data['code'], 'REAUTH_REQUIRED')
        other = Venue.objects.create(name='Tenant two', slug='daily-api-other')
        hidden = self.request(DailyCloseDetailView, close_id=close.pk, venue=other, method='get')
        self.assertEqual(hidden.status_code, 404)
        cashier = self.request(DailyCloseReviewView, close_id=close.pk, data=data, role='CASHIER')
        self.assertEqual(cashier.status_code, 403)
        reviewed = self.request(DailyCloseReviewView, close_id=close.pk, data=data)
        self.assertEqual(reviewed.status_code, 200)
        self.assertEqual(reviewed.data['status'], 'REVIEWED')

    def test_report_read_does_not_allow_generation_without_cash_review(self):
        self.membership.capability_overrides = {'allow':['management.reports.read']}
        self.membership.save(update_fields=['capability_overrides'])
        denied = self.request(DailyCloseListView, role='STAFF',
            data=dict(business_date=self.day.isoformat(), idempotency_key='forbidden'))
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(DailyClose.objects.count(), 0)

    def test_live_domain_authority_rejects_revocation_and_expired_reauth(self):
        self.session.revoked_at = timezone.now()
        self.session.save(update_fields=['revoked_at'])
        with self.assertRaises(DailyCloseError) as revoked:
            self.generate()
        self.assertEqual(revoked.exception.code, 'SESSION_REVOKED')
        self.assertEqual(DailyClose.objects.count(), 0)
        self.session.revoked_at = None
        self.session.recently_reauthenticated_at = timezone.now()-timedelta(hours=1)
        self.session.save(update_fields=['revoked_at', 'recently_reauthenticated_at'])
        with self.assertRaises(DailyCloseError) as stale:
            self.generate()
        self.assertEqual(stale.exception.code, 'REAUTH_REQUIRED')

    def test_unknown_input_rejected_and_open_tab_blocks_review(self):
        response = self.request(DailyCloseListView, data=dict(business_date=self.day.isoformat(),
            idempotency_key='strict', fabricated_payment=5000))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(DailyClose.objects.count(), 0)
        tab = Tab.objects.create(venue=self.venue)
        Tab.objects.filter(pk=tab.pk).update(opened_at=business_boundary(self.venue, self.day))
        close = self.generate()
        self.assertEqual(close.status, 'INCOMPLETE')
        self.assertTrue(any(row['kind']=='OPEN_TAB' for row in close.snapshot['blockers']))

    def test_domain_rejects_expired_access_and_mismatched_membership_actor(self):
        self.session.access_expires_at = timezone.now()-timedelta(seconds=1)
        self.session.save(update_fields=['access_expires_at'])
        with self.assertRaises(DailyCloseError) as expired:
            self.generate()
        self.assertEqual(expired.exception.code, 'ACCESS_TOKEN_EXPIRED')
        other_staff = StaffMember.objects.create(display_name='Other manager', login_identifier='daily-other-manager')
        other_membership = VenueStaffMembership.objects.create(venue=self.venue, staff_member=other_staff, role='MANAGER')
        self.session.membership = other_membership
        self.session.access_expires_at = timezone.now()+timedelta(minutes=15)
        self.session.save(update_fields=['membership', 'access_expires_at'])
        with self.assertRaises(DailyCloseError) as mismatch:
            self.generate()
        self.assertEqual(mismatch.exception.code, 'AUTH_REQUIRED')
        self.assertEqual(DailyClose.objects.count(), 0)

    @skipUnless(connection.vendor == 'postgresql', 'Requires real PostgreSQL isolation')
    def test_two_concurrent_generations_same_identity_create_one_close(self):
        barrier = Barrier(2)
        def worker(_):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return self.generate().pk
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as executor:
            ids = list(executor.map(worker, (0, 1)))
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(DailyClose.objects.count(), 1)

    @skipUnless(connection.vendor == 'postgresql', 'Requires PostgreSQL immutability trigger')
    def test_database_rejects_snapshot_and_review_mutation(self):
        close = self.generate()
        with self.assertRaises(DatabaseError), transaction.atomic():
            DailyClose.objects.filter(pk=close.pk).update(snapshot={})
        review_daily_close(close_id=close.pk, expected_version=1, reason='Checked', actor=self.actor)
        with self.assertRaises(DatabaseError), transaction.atomic():
            DailyCloseReview.objects.filter(close=close).update(reason='Rewritten')

    @skipUnless(connection.vendor == 'postgresql', 'Requires coherent PostgreSQL MVCC snapshot')
    def test_concurrent_cash_receipt_never_splits_payment_from_drawer_snapshot(self):
        from modules.venue.calendar import business_date
        self.day = business_date(self.venue)
        self.shift()
        tab = Tab.objects.create(venue=self.venue)
        barrier = Barrier(2)
        def writer():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                with transaction.atomic():
                    payment = Payment.objects.create(tab=tab, received_by=self.staff, method='CASH',
                        amount_cents=1000, idempotency_key='racing-payment', status='CONFIRMED', confirmed_at=timezone.now())
                    record_cash_payment_movement(payment_id=payment.pk, cash_point_id=self.point.pk,
                        amount_due_cents=1000, amount_tendered_cents=1000,
                        idempotency_key='racing-movement', actor=self.actor)
            finally:
                close_old_connections()
        def reader():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return self.generate().snapshot
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as executor:
            write = executor.submit(writer)
            read = executor.submit(reader)
            snapshot = read.result(timeout=20)
            write.result(timeout=20)
        paid = snapshot['receipts']['paid_cents']
        self.assertIn(paid, (0, 1000))
        self.assertEqual(snapshot['cash_shifts'][0]['expected_cents'], 5000+paid)

    @skipUnless(connection.vendor == 'postgresql', 'Requires PostgreSQL authority lock ordering')
    def test_membership_revocation_race_does_not_deadlock_admin_or_generate_after_prior_revoke(self):
        from modules.access.services import update_membership_admin
        barrier = Barrier(2)
        def revoke():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return update_membership_admin(actor_session=self.session, membership_id=self.membership.pk,
                    expected_version=1, status='REVOKED', reason='Concurrent access revocation').status
            finally:
                close_old_connections()
        def generate():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    self.generate('revocation-race')
                    return 'BEFORE_REVOKE'
                except DailyCloseError as error:
                    return error.code
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as executor:
            revocation = executor.submit(revoke)
            observation = executor.submit(generate)
            self.assertEqual(revocation.result(timeout=20), 'REVOKED')
            self.assertIn(observation.result(timeout=20), ('BEFORE_REVOKE', 'SESSION_REVOKED', 'MEMBERSHIP_REVOKED'))
        with self.assertRaises(DailyCloseError) as denied:
            self.generate('after-revoke')
        self.assertIn(denied.exception.code, ('SESSION_REVOKED', 'MEMBERSHIP_REVOKED'))
