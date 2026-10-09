"""Real canonical DispatchTask alert lifecycle, policy and tenant evidence."""
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from modules.access.models import StaffMember, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.dispatch.models import DispatchTask
from modules.management.alerts import evaluate_alerts
from modules.venue.models import Venue, OperationalAlert, OperationalAlertPolicy


class GuestRequestAlertTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name='Service', slug='service-alert')
        self.other = Venue.objects.create(name='Other', slug='service-other')
        self.staff = StaffMember.objects.create(display_name='Manager', login_identifier='service-manager')
        self.staff.set_pin('1234')
        self.staff.save()
        VenueStaffMembership.objects.create(venue=self.venue, staff_member=self.staff, role='MANAGER')
        self.now = timezone.now()
        self.task = DispatchTask.objects.create(venue=self.venue, task_type='BILL_REQUEST', destination_label='Mesa 7')
        DispatchTask.objects.filter(pk=self.task.pk).update(created_at=self.now)
        self.client = APIClient()
        login = self.client.post('/auth/login/', {'venue_slug': self.venue.slug,
            'login_identifier': self.staff.login_identifier, 'pin': '1234',
            'installation_id': 'service-alert', 'platform': 'WEB'}, format='json')
        self.assertEqual(login.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + login.data['access_token'])
        self.assertEqual(self.client.post('/auth/reauthenticate/', {'pin': '1234'}, format='json').status_code, 200)

    def test_fresh_warning_claim_escalation_terminal_resolution_and_recurrence(self):
        self.assertFalse(evaluate_alerts(self.venue, self.now + timedelta(seconds=299)).exists())
        for _ in range(10):
            evaluate_alerts(self.venue, self.now + timedelta(seconds=300))
        alert = OperationalAlert.objects.get(venue=self.venue)
        self.assertEqual(alert.severity, 'WARNING')
        self.assertEqual(alert.source['id'], str(self.task.pk))
        self.assertEqual(alert.source['target'], 'DISPATCH_TASK')
        self.assertEqual(alert.source['destination_label'], 'Mesa 7')
        self.assertEqual(alert.history.count(), 1)
        DispatchTask.objects.filter(pk=self.task.pk).update(state='CLAIMED', claimed_by=self.staff, claimed_at=self.now + timedelta(seconds=590))
        evaluate_alerts(self.venue, self.now + timedelta(seconds=600))
        alert.refresh_from_db()
        self.assertEqual(alert.severity, 'DANGER')
        self.assertEqual(alert.source['age_seconds'], 600)
        self.assertEqual(alert.source['claimed_by_id'], str(self.staff.pk))
        self.assertEqual(alert.history.filter(kind='SEVERITY_CHANGED').count(), 1)
        DispatchTask.objects.filter(pk=self.task.pk).update(state='DONE', completed_at=self.now + timedelta(seconds=601))
        evaluate_alerts(self.venue, self.now + timedelta(seconds=601))
        alert.refresh_from_db()
        self.assertEqual(alert.status, 'RESOLVED')
        self.assertEqual(alert.history.last().metadata['reason'], 'CANONICAL_CONDITION_CLEARED')
        self.task.refresh_from_db()
        self.assertEqual(self.task.state, 'DONE')
        self.assertEqual(self.task.claimed_by_id, self.staff.pk)
        new_task = DispatchTask.objects.create(venue=self.venue, task_type='BILL_REQUEST', destination_label='Mesa 7')
        DispatchTask.objects.filter(pk=new_task.pk).update(created_at=self.now)
        episode = evaluate_alerts(self.venue, self.now + timedelta(seconds=700)).get()
        self.assertNotEqual(episode.pk, alert.pk)
        self.assertEqual(episode.subject_id, new_task.pk)

    def test_only_local_service_requests_not_delivery_exception_or_terminal_tasks(self):
        DispatchTask.objects.filter(pk=self.task.pk).update(state='CANCELLED')
        for kind in ['DELIVERY', 'EXCEPTION']:
            task = DispatchTask.objects.create(venue=self.venue, task_type=kind)
            DispatchTask.objects.filter(pk=task.pk).update(created_at=self.now)
        foreign = DispatchTask.objects.create(venue=self.other, task_type='SERVICE_REQUEST')
        DispatchTask.objects.filter(pk=foreign.pk).update(created_at=self.now)
        self.assertFalse(evaluate_alerts(self.venue, self.now + timedelta(hours=1)).exists())
        self.assertEqual(evaluate_alerts(self.other, self.now + timedelta(hours=1)).get().subject_id, foreign.pk)

    def test_canonical_api_reads_provenance_and_acknowledgement_does_not_complete_task(self):
        DispatchTask.objects.filter(pk=self.task.pk).update(created_at=self.now - timedelta(seconds=650))
        response = self.client.get('/management/alerts/')
        self.assertEqual(response.status_code, 200)
        alert_id = response.data['results'][0]['id']
        detail = self.client.get(f'/management/alerts/{alert_id}/')
        self.assertEqual(detail.data['source']['source'], 'CANONICAL_DISPATCH_TASK')
        self.assertEqual(detail.data['history'][0]['metadata']['source']['id'], str(self.task.pk))
        self.assertEqual(self.client.post(f'/management/alerts/{alert_id}/', {}, format='json').status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.state, 'OPEN')
        self.assertIsNone(self.task.completed_at)
        self.assertEqual(OperationalAlert.objects.get(pk=alert_id).status, 'ACKNOWLEDGED')

    def test_typed_policy_merged_validation_audit_and_legacy_patch_preservation(self):
        values = {'expected_version': 1, 'fulfillment_warning_seconds': 600,
                  'fulfillment_danger_seconds': 1200, 'payment_pending_seconds': 300,
                  'guest_request_warning_seconds': 10, 'guest_request_danger_seconds': 20,
                  'reason': 'SLA atendimento'}
        response = self.client.patch('/management/alert-policy/', values, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['guest_request_warning_seconds'], 10)
        audit = AuditEvent.objects.get(event_type='operational_threshold.changed')
        self.assertEqual(audit.metadata['before']['guest_request_warning_seconds'], 300)
        self.assertEqual(audit.metadata['after']['guest_request_danger_seconds'], 20)
        values.update(expected_version=2, guest_request_warning_seconds=21)
        values.pop('guest_request_danger_seconds')
        self.assertEqual(self.client.patch('/management/alert-policy/', values, format='json').status_code, 400)
        self.assertEqual(OperationalAlertPolicy.objects.get(venue=self.venue).version, 2)
        values.pop('guest_request_warning_seconds')
        response = self.client.patch('/management/alert-policy/', values, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['guest_request_warning_seconds'], 10)
        self.assertEqual(response.data['guest_request_danger_seconds'], 20)


from concurrent.futures import ThreadPoolExecutor
from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase


class GuestRequestAlertConcurrencyTests(TransactionTestCase):
    def test_parallel_evaluators_preserve_one_request_episode_and_escalation(self):
        self.assertEqual(connection.vendor, 'postgresql', 'Real PostgreSQL required')
        venue = Venue.objects.create(name='Parallel service', slug='parallel-service')
        now = timezone.now()
        task = DispatchTask.objects.create(venue=venue, task_type='SERVICE_REQUEST')
        DispatchTask.objects.filter(pk=task.pk).update(created_at=now - timedelta(seconds=700))
        def worker(_):
            close_old_connections()
            try:
                return evaluate_alerts(Venue.objects.get(pk=venue.pk), now).count()
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(list(pool.map(worker, range(8))), [1] * 8)
        alert = OperationalAlert.objects.get(venue=venue)
        self.assertEqual(alert.severity, 'DANGER')
        self.assertEqual(alert.subject_id, task.pk)
        self.assertEqual(alert.history.filter(kind='ACTIVATED').count(), 1)
        task.refresh_from_db()
        self.assertEqual(task.state, 'OPEN')
