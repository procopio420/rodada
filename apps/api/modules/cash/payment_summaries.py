"""Shared PR #71 venue/day receipt contract; never a drawer balance."""
from django.db.models import Sum, Count
from modules.ledger.models import Payment, PaymentStatus, Refund, RefundStatus


def payment_method_summary(*, venue_id, day, lower, upper):
    payments = Payment.objects.filter(tab__venue_id=venue_id,
        status__in=PaymentStatus.confirmed_money_values(), confirmed_at__gte=lower,
        confirmed_at__lt=upper).values('method').annotate(paid_cents=Sum('amount_cents'), payment_count=Count('id'))
    refunds = Refund.objects.filter(payment__tab__venue_id=venue_id,
        status=RefundStatus.CONFIRMED, confirmed_at__gte=lower,
        confirmed_at__lt=upper).values('payment__method').annotate(refunds_cents=Sum('amount_cents'), refund_count=Count('id'))
    methods = {}
    def row(method):
        return methods.setdefault(method, dict(method=method, paid_cents=0, refunds_cents=0, payment_count=0, refund_count=0))
    for payment in payments:
        row(payment['method']).update(paid_cents=payment['paid_cents'], payment_count=payment['payment_count'])
    for refund in refunds:
        row(refund['payment__method']).update(refunds_cents=refund['refunds_cents'], refund_count=refund['refund_count'])
    rows = sorted(methods.values(), key=lambda value: value['method'])
    for value in rows:
        value['net_received_cents'] = value['paid_cents'] - value['refunds_cents']
    paid = sum(value['paid_cents'] for value in rows)
    refunded = sum(value['refunds_cents'] for value in rows)
    return dict(scope='VENUE_BUSINESS_DATE', business_date=day.isoformat(),
        paid_cents=paid, refunds_cents=refunded, net_received_cents=paid-refunded, methods=rows)
