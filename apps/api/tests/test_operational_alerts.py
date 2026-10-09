from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from django.db import close_old_connections, connection, connections
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient
from modules.access.models import StaffMember, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.catalog.models import Product
from modules.ordering.models import Tab, Order, OrderItem
from modules.cash.models import CashPoint, CashShift
from modules.ledger.models import Payment
from modules.venue.models import Venue, OperationalAlert, OperationalAlertPolicy
from modules.management.alerts import evaluate_alerts

class AlertFixtures:
    def setup_facts(self):
        self.venue = Venue.objects.create(name='Alert bar', slug='alert-bar')
        self.other = Venue.objects.create(name='Other', slug='other-alert-bar')
        self.staff = StaffMember.objects.create(display_name='Manager', login_identifier='alert-manager')
        self.staff.set_pin('1234')
        self.staff.save()
        VenueStaffMembership.objects.create(venue=self.venue, staff_member=self.staff, role='MANAGER')
        self.tab = Tab.objects.create(venue=self.venue)
        self.product = Product.objects.create(venue=self.venue, name='Fritas', price_cents=1000, fulfillment_station='KITCHEN')
        self.order = Order.objects.create(tab=self.tab, source='STAFF')
        self.item = OrderItem.objects.create(order=self.order, product=self.product, product_name_snapshot='Fritas', unit_price_cents=1000, quantity=1, fulfillment_station_snapshot='KITCHEN')
        self.now = timezone.now()
        OrderItem.objects.filter(pk=self.item.pk).update(created_at=self.now-timedelta(seconds=700))


class OperationalAlertTests(AlertFixtures, TestCase):
    def setUp(self):
        self.setup_facts()
        self.client = APIClient()
        response = self.client.post('/auth/login/', {'venue_slug': self.venue.slug, 'login_identifier': self.staff.login_identifier,
            'pin': '1234', 'installation_id': 'alert-test', 'platform': 'WEB'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+response.json()['access_token'])
        self.assertEqual(self.client.post('/auth/reauthenticate/', {'pin':'1234'}, format='json').status_code, 200)

    def test_dedupe_escalation_resolution_recurrence_and_provenance(self):
        for _ in range(10): evaluate_alerts(self.venue, self.now)
        alert = OperationalAlert.objects.get(venue=self.venue)
        self.assertEqual(alert.severity, 'WARNING')
        self.assertEqual(alert.source['station'], 'KITCHEN')
        self.assertEqual(alert.history.count(), 1)
        evaluate_alerts(self.venue, self.now+timedelta(seconds=600))
        alert.refresh_from_db()
        self.assertEqual(alert.severity, 'DANGER')
        self.assertEqual(alert.history.count(), 2)
        OrderItem.objects.filter(pk=self.item.pk).update(state='DELIVERED')
        evaluate_alerts(self.venue, self.now+timedelta(seconds=601))
        alert.refresh_from_db()
        self.assertEqual(alert.status, 'RESOLVED')
        OrderItem.objects.filter(pk=self.item.pk).update(state='NEW')
        evaluate_alerts(self.venue, self.now+timedelta(seconds=602))
        episode = OperationalAlert.objects.exclude(pk=alert.pk).get()
        self.assertEqual(episode.repeat_of_id, alert.pk)
        self.assertEqual(alert.history.last().metadata['reason'], 'CANONICAL_CONDITION_CLEARED')

    def test_cash_ack_is_idempotent_not_resolution_then_review_resolves(self):
        point = CashPoint.objects.create(venue=self.venue, label='Caixa')
        shift = CashShift.objects.create(venue=self.venue, cash_point=point, business_date=self.now.date(),
            opened_by=self.staff, opening_idempotency_key='open', status='CLOSED', review_status='PENDING', discrepancy_cents=-100)
        alert = evaluate_alerts(self.venue, self.now).get(rule_key='CASH_DISCREPANCY')
        for _ in range(2):
            response = self.client.post(f'/management/alerts/{alert.pk}/', {}, format='json')
            self.assertEqual(response.status_code, 200, response.data)
        alert.refresh_from_db()
        self.assertEqual(alert.status, 'ACKNOWLEDGED')
        self.assertIsNone(alert.resolved_at)
        self.assertEqual(alert.history.filter(kind='ACKNOWLEDGED').count(), 1)
        self.assertEqual(AuditEvent.objects.filter(event_type='alert.acknowledged').count(), 1)
        CashShift.objects.filter(pk=shift.pk).update(review_status='REVIEWED')
        evaluate_alerts(self.venue, self.now)
        alert.refresh_from_db()
        self.assertEqual(alert.status, 'RESOLVED')

    def test_pending_payment_resolution_and_no_normal_payment_noise(self):
        payment = Payment.objects.create(tab=self.tab, amount_cents=500, method='TAP_TO_PAY', idempotency_key='pending', received_by=self.staff, status='CONFIRMATION_PENDING')
        Payment.objects.filter(pk=payment.pk).update(received_at=self.now-timedelta(seconds=301))
        alert = evaluate_alerts(self.venue, self.now).get(rule_key='PAYMENT_PENDING')
        Payment.objects.filter(pk=payment.pk).update(status='FAILED')
        evaluate_alerts(self.venue, self.now)
        alert.refresh_from_db()
        self.assertEqual(alert.status, 'RESOLVED')
        self.assertFalse(evaluate_alerts(self.venue, self.now).filter(rule_key='PAYMENT_PENDING').exists())

    def test_threshold_validation_conflict_and_audit(self):
        self.assertEqual(self.client.get('/management/alert-policy/').json()['section'], 'operational_alerts')
        values = {'expected_version':1, 'fulfillment_warning_seconds': 300, 'fulfillment_danger_seconds':600, 'payment_pending_seconds':200, 'reason':'Pico'}
        first = self.client.patch('/management/alert-policy/', values, format='json')
        self.assertEqual(first.status_code, 200, first.data)
        stale = self.client.patch('/management/alert-policy/', values, format='json')
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(stale.data['current']['version'], 2)
        values.update(expected_version=2, fulfillment_warning_seconds=700)
        self.assertEqual(self.client.patch('/management/alert-policy/', values, format='json').status_code, 400)
        self.assertEqual(AuditEvent.objects.get(event_type='operational_threshold.changed').reason, 'Pico')

    def test_cross_venue_idor_and_revoked_capability(self):
        alert = OperationalAlert.objects.create(venue=self.other, rule_key='CASH_DISCREPANCY', rule_version=1,
            subject_id=self.item.id, severity='DANGER', source={}, first_detected_at=self.now, updated_at=self.now)
        self.assertEqual(self.client.get(f'/management/alerts/{alert.id}/').status_code, 404)
        self.assertEqual(self.client.post(f'/management/alerts/{alert.id}/', {}, format='json').status_code, 404)
        VenueStaffMembership.objects.filter(venue=self.venue, staff_member=self.staff).update(role='STAFF')
        self.assertEqual(self.client.get('/management/alerts/').status_code, 403)

    def test_report_never_counts_pending_payment_as_received(self):
        from modules.venue.calendar import business_date
        Payment.objects.create(tab=self.tab, amount_cents=500, method='TAP_TO_PAY', idempotency_key='ambiguous-report', received_by=self.staff, status='CONFIRMATION_PENDING')
        date = business_date(self.venue)
        response = self.client.get(f'/management/reports/?start={date}&end={date}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['totals']['paid_cents'], 0)
        self.assertEqual(response.data['payment_methods'], [])

    def test_calendar_history_cannot_be_reassigned(self):
        from modules.ledger.models import Charge
        from modules.venue.calendar import business_date
        Charge.objects.create(tab=self.tab, order_item=self.item, amount_cents=1000)
        before = business_date(self.venue, self.item.created_at)
        response = self.client.patch('/management/calendar/', {'timezone':'America/Sao_Paulo', 'cutoff_hour':6}, format='json')
        self.assertEqual(response.status_code, 409, response.data)
        self.assertIn('CHARGE_HISTORY', response.data['blockers'])
        self.venue.refresh_from_db()
        self.assertEqual(business_date(self.venue, self.item.created_at), before)
        self.assertEqual(self.venue.business_day_cutoff_hour, 0)

    def test_policy_change_requires_recent_reauthentication(self):
        from modules.access.models import StaffSession
        StaffSession.objects.filter(venue=self.venue).update(recently_reauthenticated_at=None)
        response = self.client.patch('/management/alert-policy/', {}, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['code'], 'REAUTH_REQUIRED')

    def test_strategic_product_resolution_recurrence_and_noise_control(self):
        from modules.catalog.models import ProductAvailability
        ProductAvailability.objects.filter(product=self.product).update(state='UNAVAILABLE')
        self.assertFalse(evaluate_alerts(self.venue, self.now).filter(rule_key='STRATEGIC_PRODUCT').exists())
        policy = OperationalAlertPolicy.objects.get(venue=self.venue)
        policy.strategic_products.add(self.product)
        alert = evaluate_alerts(self.venue, self.now).get(rule_key='STRATEGIC_PRODUCT')
        ProductAvailability.objects.filter(product=self.product).update(state='AVAILABLE')
        evaluate_alerts(self.venue, self.now)
        alert.refresh_from_db()
        self.assertEqual(alert.status, 'RESOLVED')
        ProductAvailability.objects.filter(product=self.product).update(state='UNAVAILABLE')
        episode = evaluate_alerts(self.venue, self.now).get(rule_key='STRATEGIC_PRODUCT')
        self.assertEqual(episode.repeat_of_id, alert.pk)

    def test_stage_age_and_terminal_exclusion(self):
        OrderItem.objects.filter(pk=self.item.pk).update(state='READY', ready_at=self.now)
        self.assertEqual(evaluate_alerts(self.venue, self.now).count(), 0)
        OrderItem.objects.filter(pk=self.item.pk).update(state='CANCELLED')
        self.assertEqual(evaluate_alerts(self.venue, self.now+timedelta(hours=1)).count(), 0)


class OperationalAlertConcurrencyTests(AlertFixtures, TransactionTestCase):
    def setUp(self): self.setup_facts()

    def test_parallel_evaluators_create_one_episode(self):
        self.assertEqual(connection.vendor, 'postgresql', 'Real PostgreSQL required for lock evidence')
        def worker(_):
            close_old_connections()
            try: return evaluate_alerts(Venue.objects.get(pk=self.venue.pk), self.now).count()
            finally: connections.close_all()
        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(list(pool.map(worker, range(8))), [1]*8)
        self.assertEqual(OperationalAlert.objects.filter(venue=self.venue).count(), 1)
