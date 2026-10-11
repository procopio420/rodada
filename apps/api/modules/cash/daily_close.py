"""Coherent as-of snapshots, immutable revisions and separate reviews."""
import hashlib
import json
from datetime import timedelta
from django.db import connection, transaction, OperationalError, IntegrityError
from django.db.models import Max, Sum
from django.utils import timezone
from modules.audit.services import record_audit_event
from modules.venue.models import Venue
from modules.venue.calendar import business_boundary
from modules.ordering.models import Tab
from modules.ledger.models import Charge, LedgerAdjustment, Payment, PaymentStatus, Refund
from modules.cash.models import DailyClose, DailyCloseReview, CashShift, CashMovement, CashCorrectionRequest
from modules.cash.services import cash_shift_position
from modules.cash.payment_summaries import payment_method_summary


class DailyCloseError(Exception):
    def __init__(self, code, message, status_code=409):
        self.code, self.message, self.status_code = code, message, status_code
        super().__init__(message)


def _digest(snapshot):
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _authorize(actor):
    from modules.access.models import StaffSession, DeviceRegistration
    from modules.access.capabilities import Capability, has_capability
    from modules.access.services import _session_failure, recent_reauthentication_valid
    # Lock only the session. Admin changes lock membership/device before
    # updating sessions; locking those rows here after session would invert
    # their order. Authority reads share this transaction's MVCC boundary and
    # may linearize before a concurrent revocation, never after a prior commit.
    session = StaffSession.objects.select_related('membership', 'staff_member').select_for_update(of=('self',)).filter(
        pk=actor.session_id, venue_id=actor.venue_id, staff_member_id=actor.staff_id).first()
    if session is None or session.device_id != actor.device_id:
        raise DailyCloseError('AUTH_REQUIRED', 'Sessão válida necessária.', 401)
    if session.device_id:
        session.device = DeviceRegistration.objects.get(pk=session.device_id)
        if session.device.venue_id != session.venue_id:
            raise DailyCloseError('AUTH_REQUIRED', 'Dispositivo fora deste estabelecimento.', 401)
    if session.membership.staff_member_id != session.staff_member_id:
        raise DailyCloseError('AUTH_REQUIRED', 'Vínculo de operador inválido.', 401)
    failure = _session_failure(session)
    if failure:
        raise DailyCloseError(failure.code, failure.message, failure.status_code)
    if not session.access_expires_at or session.access_expires_at <= timezone.now():
        raise DailyCloseError('ACCESS_TOKEN_EXPIRED', 'Renove a sessão antes de continuar.', 401)
    if not has_capability(session.membership, Capability.CASH_REVIEW):
        raise DailyCloseError('CAPABILITY_REQUIRED', 'Revisão financeira não autorizada.', 403)
    if not recent_reauthentication_valid(session):
        raise DailyCloseError('REAUTH_REQUIRED', 'Confirme seu PIN novamente.', 403)


def _snapshot(venue, day):
    lower, upper = business_boundary(venue, day), business_boundary(venue, day + timedelta(days=1))
    shifts = list(CashShift.objects.filter(venue=venue, business_date=day).select_related('cash_point').order_by('id'))
    shift_rows, blockers = [], []
    for shift in shifts:
        shift_rows.append(dict(id=str(shift.id), cash_point_id=str(shift.cash_point_id),
            label=shift.cash_point.label, status=shift.status, version=shift.version,
            review_status=shift.review_status, **cash_shift_position(shift)))
        if shift.status != 'CLOSED' or shift.review_status == 'PENDING':
            blockers.append(dict(kind='CASH_SHIFT', id=str(shift.id), status=shift.status, review_status=shift.review_status))
    # An undecided cash proposal is not a committed movement; it blocks a
    # reviewed close until a different manager approves or rejects it.
    for proposal in CashCorrectionRequest.objects.filter(
        shift__venue=venue, shift__business_date=day, status="PENDING"
    ).order_by("id"):
        blockers.append(dict(kind="PENDING_CASH_CORRECTION", id=str(proposal.id),
            shift_id=str(proposal.shift_id), amount_cents=proposal.amount_cents))
    # A shift from an earlier service still blocks honest reconciliation today.
    for shift in CashShift.objects.filter(venue=venue, business_date__lt=day, status__in=('OPEN', 'COUNTING')).order_by('id'):
        blockers.append(dict(kind='OVERDUE_CASH_SHIFT', id=str(shift.id), business_date=shift.business_date.isoformat(), status=shift.status))
    pending = Payment.objects.filter(tab__venue=venue, received_at__lt=upper,
        status__in=('CREATED', 'PENDING', 'PROCESSING', 'AUTHORIZED', 'CONFIRMATION_PENDING')).order_by('id')
    for payment in pending:
        blockers.append(dict(kind='UNRESOLVED_PAYMENT', id=str(payment.id), tab_id=str(payment.tab_id), status=payment.status))
    if upper > timezone.now():
        blockers.append(dict(kind='BUSINESS_DAY_NOT_ENDED'))
    from modules.ledger.services import totals
    tabs = [dict(id=str(tab.id), version=tab.version, state=tab.state,
        exposure_cents=totals(tab)['exposure_cents']) for tab in Tab.objects.filter(
            venue=venue, opened_at__lt=upper).exclude(state__in=('CLOSED', 'CANCELLED')).order_by('id')]
    for tab in tabs:
        blockers.append(dict(kind='OPEN_TAB', id=tab['id'], exposure_cents=tab['exposure_cents']))
    charges = Charge.objects.filter(tab__venue=venue, created_at__gte=lower, created_at__lt=upper)
    adjustments = LedgerAdjustment.objects.filter(tab__venue=venue, created_at__gte=lower, created_at__lt=upper)
    aggregate = lambda rows: rows.aggregate(value=Sum('amount_cents'))['value'] or 0
    gross, adjustment = aggregate(charges), aggregate(adjustments)
    from modules.ledger.pricing import category
    service_pass_through = 0
    for fact in adjustments.select_related('reverses'):
        if category(fact) == 'service':
            allocations = fact.policy_snapshot.get('service_allocations')
            if allocations is not None:
                service_pass_through += sum(value.get('service_pass_through', 0) for value in allocations.values())
            else:
                policy = fact.reverses.policy_snapshot if fact.kind == 'REVERSAL' else fact.policy_snapshot
                if policy.get('service_treatment', 'PASS_THROUGH') != 'REVENUE':
                    service_pass_through += fact.amount_cents
    facts = dict(charge_ids=[str(value) for value in charges.order_by('id').values_list('id', flat=True)],
        adjustment_ids=[str(value) for value in adjustments.order_by('id').values_list('id', flat=True)],
        movement_ids=[str(value) for value in CashMovement.objects.filter(shift__in=shifts).order_by('id').values_list('id', flat=True)],
        payment_ids=[str(value) for value in Payment.objects.filter(tab__venue=venue,
            status__in=PaymentStatus.confirmed_money_values(), confirmed_at__gte=lower,
            confirmed_at__lt=upper).order_by('id').values_list('id', flat=True)],
        refund_ids=[str(value) for value in Refund.objects.filter(payment__tab__venue=venue,
            status='CONFIRMED', confirmed_at__gte=lower, confirmed_at__lt=upper).order_by('id').values_list('id', flat=True)])
    return dict(schema_version=1, business_date=day.isoformat(),
        calendar=dict(timezone=venue.timezone, cutoff_hour=venue.business_day_cutoff_hour,
            lower=lower.isoformat(), upper=upper.isoformat()),
        financial=dict(gross_cents=gross, adjustments_cents=adjustment, payable_cents=gross+adjustment,
            service_pass_through_cents=service_pass_through, net_sales_cents=gross+adjustment-service_pass_through),
        receipts=payment_method_summary(venue_id=venue.id, day=day, lower=lower, upper=upper),
        open_tabs=tabs, cash_shifts=shift_rows, blockers=blockers, facts=facts)


def _coherent(operation):
    # This must own the transaction: SET TRANSACTION after an earlier query is
    # invalid and READ COMMITTED would mix two different financial boundaries.
    if connection.vendor == 'postgresql' and connection.in_atomic_block:
        raise DailyCloseError('TRANSACTION_BOUNDARY_REQUIRED', 'Fechamento exige transação própria.', 503)
    for attempt in range(3):
        try:
            with transaction.atomic():
                if connection.vendor == 'postgresql':
                    with connection.cursor() as cursor:
                        cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
                return operation()
        except (OperationalError, IntegrityError) as error:
            code = getattr(error.__cause__, 'sqlstate', None) or getattr(error.__cause__, 'pgcode', None)
            if code not in ('40001', '40P01', '23505'):
                raise
            if attempt == 2:
                raise DailyCloseError('RETRY_REQUIRED', 'Fechamento mudou durante a operação. Tente novamente.', 409) from error


def generate_daily_close(*, day, idempotency_key, actor):
    if not idempotency_key or len(idempotency_key) > 120:
        raise DailyCloseError('IDEMPOTENCY_KEY_REQUIRED', 'Informe uma chave válida.', 400)
    def operation():
        # Shared configuration/release lock order is Venue -> authority rows.
        # NO KEY UPDATE remains compatible with financial FK KEY SHARE locks.
        venue = Venue.objects.select_for_update(no_key=True).get(pk=actor.venue_id)
        _authorize(actor)
        existing = DailyClose.objects.filter(venue=venue, idempotency_key=idempotency_key).first()
        if existing:
            if existing.business_date != day:
                raise DailyCloseError('IDEMPOTENCY_CONFLICT', 'Chave usada em outro dia.')
            return existing
        snapshot = _snapshot(venue, day)
        version = (DailyClose.objects.filter(venue=venue, business_date=day).aggregate(value=Max('version'))['value'] or 0) + 1
        close = DailyClose.objects.create(venue=venue, business_date=day, version=version,
            generated_at=timezone.now(), generated_by_id=actor.staff_id, idempotency_key=idempotency_key,
            status='INCOMPLETE' if snapshot['blockers'] else 'READY_FOR_REVIEW',
            snapshot=snapshot, fingerprint=_digest(snapshot))
        record_audit_event(actor=actor, event_type='daily_close.generated', entity_type='DailyClose',
            entity_id=str(close.id), metadata=dict(version=version, fingerprint=close.fingerprint, status=close.status))
        return close
    return _coherent(operation)


def review_daily_close(*, close_id, expected_version, reason, actor):
    if not reason.strip():
        raise DailyCloseError('REVIEW_REASON_REQUIRED', 'Informe o motivo.', 400)
    def operation():
        venue = Venue.objects.select_for_update(no_key=True).get(pk=actor.venue_id)
        _authorize(actor)
        close = DailyClose.objects.filter(pk=close_id, venue=venue).first()
        if close is None:
            raise DailyCloseError('DAILY_CLOSE_NOT_FOUND', 'Fechamento não encontrado.', 404)
        if expected_version != close.version:
            raise DailyCloseError('STALE_VERSION', 'Atualize a versão do fechamento.')
        review = DailyCloseReview.objects.filter(close=close).first()
        if review:
            if review.reason != reason.strip():
                raise DailyCloseError('ALREADY_REVIEWED', 'Revisão já registrada.')
            return close
        if close.status != 'READY_FOR_REVIEW':
            raise DailyCloseError('DAILY_CLOSE_INCOMPLETE', 'Resolva os bloqueios e gere uma nova revisão.')
        if _digest(_snapshot(venue, close.business_date)) != close.fingerprint:
            raise DailyCloseError('STALE_SNAPSHOT', 'Os fatos mudaram. Gere uma nova revisão.')
        review = DailyCloseReview.objects.create(close=close, reviewed_by_id=actor.staff_id,
            reviewed_at=timezone.now(), reason=reason.strip(), fingerprint=close.fingerprint)
        record_audit_event(actor=actor, event_type='daily_close.reviewed', entity_type='DailyClose',
            entity_id=str(close.id), reason=review.reason, metadata=dict(version=close.version, fingerprint=close.fingerprint))
        return close
    return _coherent(operation)
