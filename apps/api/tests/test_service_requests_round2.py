import uuid
from concurrent.futures import ThreadPoolExecutor
from django.db import close_old_connections
from django.test import TransactionTestCase
from django.utils import timezone
from modules.audit.models import AuditEvent
from modules.access.context import ActorContext
from modules.access.models import StaffMember
from modules.dispatch.services import DispatchServiceError, update_service_request
from modules.guest_access.models import GuestSession
from modules.dispatch.models import DispatchTask
from modules.dispatch.services import create_service_request
from modules.guest_access.services import resolve_table_qr
from modules.hospitality.models import GuestOrderingMode, Table, TableOccupancy, TableStatus
from tests.test_dispatch import DispatchFoundationTests


class ServiceRequestRound2Tests(DispatchFoundationTests):
    def visit(self):
        table = Table.objects.create(venue=self.venue, label='Requests', status=TableStatus.OCCUPIED,
                                     guest_ordering_mode=GuestOrderingMode.JOIN_ACTIVE)
        occupancy = TableOccupancy.objects.create(table=table, generation=table.access_generation)
        return table, occupancy

    def test_guest_request_claim_complete_retry_and_revocation(self):
        table, occupancy = self.visit()
        guest = resolve_table_qr(public_token=table.public_token)
        client = self.client.__class__()
        client.credentials(HTTP_X_GUEST_SESSION=guest.token)
        data = {'request_id': str(uuid.uuid4()), 'task_type': 'BILL_REQUEST'}
        first = client.post('/guest/service-requests/', data, format='json')
        assert first.status_code == 201, first.json()
        assert set(first.json()) == {'id', 'task_type', 'state'}
        task_id = data['request_id']
        assert self.client.get('/dispatch/requests/').json()['results'][0]['id'] == task_id
        claim = self.client.post(f'/dispatch/requests/{task_id}/claim/', {}, format='json')
        assert claim.status_code == 200
        assert claim.json()['state'] == 'CLAIMED'
        assert self.client.post(f'/dispatch/requests/{task_id}/complete/', {}, format='json').status_code == 200
        replay = client.post('/guest/service-requests/', data, format='json')
        assert replay.status_code == 200
        assert replay.json()['state'] == 'DONE'
        assert AuditEvent.objects.filter(entity_id=task_id).count() == 3
        assert self.client.get('/dispatch/requests/').json()['results'] == []
        table.access_generation += 1
        table.save()
        assert client.post('/guest/service-requests/', data, format='json').status_code == 403
        assert DispatchTask.objects.count() == 1

    def test_expired_guest_and_claim_ownership_are_enforced(self):
        table, _ = self.visit()
        guest = resolve_table_qr(public_token=table.public_token)
        GuestSession.objects.filter(pk=guest.session.id).update(expires_at=timezone.now())
        client = self.client.__class__()
        client.credentials(HTTP_X_GUEST_SESSION=guest.token)
        assert client.post('/guest/service-requests/', {
            'request_id': str(uuid.uuid4()), 'task_type': 'BILL_REQUEST'
        }, format='json').status_code == 401
        task = create_service_request(request_id=uuid.uuid4(), task_type='BILL_REQUEST',
                                      table_id=table.id, actor=self.actor)
        update_service_request(task_id=task.id, actor=self.actor)
        other_staff = StaffMember.objects.create(display_name='Other', login_identifier='request-other')
        other = ActorContext(venue_id=self.venue.id, staff_id=other_staff.id,
                             session_id=self.actor.session_id, device_id=None)
        for complete in (False, True):
            with self.assertRaises(DispatchServiceError) as error:
                update_service_request(task_id=task.id, actor=other, complete=complete)
            assert error.exception.code == 'SERVICE_TASK_ALREADY_CLAIMED'
        task.refresh_from_db()
        assert task.state == 'CLAIMED'
        assert task.claimed_by_id == self.staff.id

    def test_staff_idempotency_conflict_and_cross_venue(self):
        table, _ = self.visit()
        payload = {'table_id': str(table.id), 'request_id': str(uuid.uuid4()), 'task_type': 'SERVICE_REQUEST'}
        assert self.client.post('/dispatch/requests/', payload, format='json').status_code == 201
        assert self.client.post('/dispatch/requests/', payload, format='json').status_code == 200
        payload['task_type'] = 'BILL_REQUEST'
        assert self.client.post('/dispatch/requests/', payload, format='json').status_code == 409
        other = Table.objects.create(venue=self.other_venue, label='Private')
        payload['table_id'] = str(other.id)
        payload['request_id'] = str(uuid.uuid4())
        assert self.client.post('/dispatch/requests/', payload, format='json').status_code == 404
        assert DispatchTask.objects.count() == 1

    def test_completion_without_claim_is_retry_safe(self):
        table, _ = self.visit()
        task = create_service_request(request_id=uuid.uuid4(), task_type='SERVICE_REQUEST',
                                      table_id=table.id, actor=self.actor)
        for _ in range(2):
            assert self.client.post(f'/dispatch/requests/{task.id}/complete/', {}, format='json').status_code == 200
        task.refresh_from_db()
        assert task.state == 'DONE'
        assert task.claimed_at is None
        assert AuditEvent.objects.filter(entity_id=str(task.id), event_type='dispatch.service_completed').count() == 1


class ServiceRequestConcurrencyTests(TransactionTestCase):
    setUp = DispatchFoundationTests.setUp

    def test_concurrent_same_request_creates_one_task_and_audit(self):
        table = Table.objects.create(venue=self.venue, label='Concurrent', status=TableStatus.OCCUPIED)
        TableOccupancy.objects.create(table=table, generation=table.access_generation)
        request_id = uuid.uuid4()
        def create(_):
            close_old_connections()
            try:
                return create_service_request(request_id=request_id, task_type='BILL_REQUEST',
                                              table_id=table.id, actor=self.actor).id
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(create, range(2)))
        assert results == [request_id, request_id]
        assert DispatchTask.objects.filter(pk=request_id).count() == 1
        assert AuditEvent.objects.filter(event_type='dispatch.service_requested').count() == 1
