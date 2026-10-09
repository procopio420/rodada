"""Canonical exception projection. Serializes evaluators per Venue, never mutates sources.

Push delivery is deliberately absent: persisted in-app episodes are not proof of push.
"""
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from modules.venue.models import Venue, OperationalAlertPolicy, OperationalAlert, OperationalAlertEvent
from modules.ordering.models import OrderItem
from modules.ledger.models import Payment
from modules.cash.models import CashShift
from modules.realtime.services import emit_event


def _event(alert, kind, now, **metadata):
    OperationalAlertEvent.objects.create(alert=alert, kind=kind, occurred_at=now, metadata=metadata)
    emit_event(venue_id=alert.venue_id, event_type='alert.' + kind.lower(),
               aggregate_type='OperationalAlert', aggregate_id=alert.id)


@transaction.atomic
def evaluate_alerts(venue, now=None):
    now = now or timezone.now()
    Venue.objects.select_for_update().get(pk=venue.pk)
    policy, _ = OperationalAlertPolicy.objects.get_or_create(venue=venue)
    conditions = {}
    items = OrderItem.objects.filter(order__tab__venue=venue).select_related('product').exclude(state__in=['DELIVERED', 'CANCELLED'])
    for item in items:
        stage_at = {'ACCEPTED': item.accepted_at, 'PREPARING': item.preparing_at,
                    'READY': item.ready_at, 'PICKED_UP': item.picked_up_at}.get(item.state) or item.created_at
        age = max(0, int((now - stage_at).total_seconds()))
        if age >= policy.fulfillment_warning_seconds:
            conditions[('FULFILLMENT_SLA', item.id)] = (
                'DANGER' if age >= policy.fulfillment_danger_seconds else 'WARNING', stage_at,
                {'target': 'FULFILLMENT_ITEM', 'id': str(item.id), 'station': item.fulfillment_station_snapshot or item.product.fulfillment_station,
                 'state': item.state, 'age_seconds': age, 'stage_started_at': stage_at.isoformat(), 'source': 'CANONICAL_TIMESTAMP'})
    for payment in Payment.objects.filter(tab__venue=venue, status='CONFIRMATION_PENDING',
                                          received_at__lte=now - timedelta(seconds=policy.payment_pending_seconds)):
        conditions[('PAYMENT_PENDING', payment.id)] = ('DANGER', payment.received_at,
            {'target': 'PAYMENT', 'id': str(payment.id), 'tab_id': str(payment.tab_id), 'source': 'CANONICAL_PAYMENT_STATE'})
    for shift in CashShift.objects.filter(venue=venue, status='CLOSED', review_status='PENDING'):
        conditions[('CASH_DISCREPANCY', shift.id)] = ('DANGER', shift.closed_at or shift.opened_at,
            {'target': 'CASH_SHIFT', 'id': str(shift.id), 'source': 'CANONICAL_CASH_REVIEW'})
    for product in policy.strategic_products.filter(venue=venue, availability__state='UNAVAILABLE'):
        conditions[('STRATEGIC_PRODUCT', product.id)] = ('WARNING', now,
            {'target': 'PRODUCT', 'id': str(product.id), 'source': 'CANONICAL_PRODUCT_AVAILABILITY'})
    active = {(a.rule_key, a.subject_id): a for a in OperationalAlert.objects.filter(venue=venue).exclude(status='RESOLVED')}
    for key, (severity, source_at, source) in conditions.items():
        alert = active.pop(key, None)
        if alert is None:
            previous = OperationalAlert.objects.filter(venue=venue, rule_key=key[0], subject_id=key[1]).order_by('-resolved_at').first()
            alert = OperationalAlert.objects.create(venue=venue, rule_key=key[0], subject_id=key[1], rule_version=policy.version,
                severity=severity, source=source, first_detected_at=now, updated_at=now, repeat_of=previous)
            _event(alert, 'ACTIVATED', now, source_at=source_at.isoformat(), rule_version=policy.version, source=source, severity=severity)
        else:
            if alert.severity == 'WARNING' and severity == 'DANGER':
                alert.severity = severity
                _event(alert, 'SEVERITY_CHANGED', now, before='WARNING', after='DANGER', rule_version=policy.version)
            alert.source, alert.updated_at = source, now
            alert.save(update_fields=['source', 'updated_at', 'severity'])
    for alert in active.values():
        alert.status, alert.resolved_at, alert.updated_at = 'RESOLVED', now, now
        alert.save(update_fields=['status', 'resolved_at', 'updated_at'])
        _event(alert, 'RESOLVED', now, reason='CANONICAL_CONDITION_CLEARED', rule_version=policy.version)
    return OperationalAlert.objects.filter(venue=venue).exclude(status='RESOLVED')


def payload(alert):
    return {'id': str(alert.id), 'rule_key': alert.rule_key, 'rule_version': alert.rule_version,
            'severity': alert.severity, 'status': alert.status, 'source': alert.source,
            'first_detected_at': alert.first_detected_at, 'updated_at': alert.updated_at,
            'acknowledged_at': alert.acknowledged_at, 'resolved_at': alert.resolved_at,
            'repeat_of': str(alert.repeat_of_id) if alert.repeat_of_id else None}
