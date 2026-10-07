"""Transactional application services for the Core POS."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone

from audit.models import AuditEvent
from cash.models import CashShift
from ledger.models import Adjustment, Charge, Payment
from pos.models import Order, OrderItem, StaffMember, Tab


def _audit(actor, action, instance, *, reason="", before=None, after=None):
    venue = instance.venue if hasattr(instance, "venue") else instance.order.tab.venue if hasattr(instance, "order") else instance.tab.venue
    AuditEvent.objects.create(venue=venue,
        actor=actor, action=action, entity_type=instance._meta.label, entity_id=instance.pk,
        reason=reason, before=before or {}, after=after or {})


def exposure_cents(tab):
    charges = tab.charges.aggregate(total=Sum("amount_cents"))["total"] or 0
    payments = tab.payments.filter(status=Payment.Status.CONFIRMED).aggregate(total=Sum("amount_cents"))["total"] or 0
    adjustments = tab.adjustments.aggregate(total=Sum("amount_cents"))["total"] or 0
    return charges - payments + adjustments


@transaction.atomic
def confirm_order(order_id, actor):
    order = Order.objects.select_for_update().select_related("tab", "tab__venue").prefetch_related("items__product").get(pk=order_id)
    if order.status == Order.Status.CONFIRMED:
        return order
    if actor.venue_id != order.tab.venue_id:
        raise PermissionDenied("Staff member does not belong to this venue.")
    if order.status != Order.Status.DRAFT or order.tab.status != Tab.Status.OPEN:
        raise ValidationError("Order cannot be confirmed.")
    if not order.items.exists(): raise ValidationError("An order needs at least one item.")
    for item in order.items.all():
        if item.product.venue_id != order.tab.venue_id: raise ValidationError("Product does not belong to the tab venue.")
        if not item.product.active or not item.product.available: raise ValidationError(f"Product {item.product.name} is unavailable.")
        item.unit_price_cents = item.product.current_price_cents
        item.fulfillment_station = item.product.fulfillment_station
        item.save(update_fields=["unit_price_cents", "fulfillment_station"])
        Charge.objects.get_or_create(tab=order.tab, order_item=item, defaults={"amount_cents": item.unit_price_cents * item.quantity})
    order.status, order.confirmed_at = Order.Status.CONFIRMED, timezone.now()
    order.save(update_fields=["status", "confirmed_at"])
    if exposure_cents(order.tab) >= order.tab.operating_limit_cents:
        order.tab.status = Tab.Status.REQUIRES_ACTION
        order.tab.save(update_fields=["status"])
    _audit(actor, "order.confirmed", order, after={
        "item_count": order.items.count(),
        "charges_cents": sum(item.unit_price_cents * item.quantity for item in order.items.all()),
    })
    return order


_TRANSITIONS = {
    OrderItem.State.NEW: {OrderItem.State.ACCEPTED, OrderItem.State.CANCELLED},
    OrderItem.State.ACCEPTED: {OrderItem.State.PREPARING, OrderItem.State.READY, OrderItem.State.CANCELLED},
    OrderItem.State.PREPARING: {OrderItem.State.READY, OrderItem.State.CANCELLED},
    OrderItem.State.READY: {OrderItem.State.PICKED_UP, OrderItem.State.DELIVERED, OrderItem.State.CANCELLED},
    OrderItem.State.PICKED_UP: {OrderItem.State.DELIVERED, OrderItem.State.CANCELLED},
    OrderItem.State.DELIVERED: set(), OrderItem.State.CANCELLED: set(),
}
_TIMESTAMPS = {OrderItem.State.ACCEPTED: "accepted_at", OrderItem.State.PREPARING: "preparing_at", OrderItem.State.READY: "ready_at", OrderItem.State.PICKED_UP: "picked_up_at", OrderItem.State.DELIVERED: "delivered_at"}


@transaction.atomic
def transition_order_item(item_id, target, actor, reason=""):
    item = OrderItem.objects.select_for_update().select_related("order__tab__venue").get(pk=item_id)
    if actor.venue_id != item.order.tab.venue_id: raise PermissionDenied("Staff member does not belong to this venue.")
    if item.order.tab.status == Tab.Status.CLOSED: raise ValidationError("Cannot change fulfillment on a closed tab.")
    if target == OrderItem.State.CANCELLED:
        return cancel_order_item(item_id, actor, reason)
    if target not in _TRANSITIONS[item.state]: raise ValidationError(f"Transition {item.state} -> {target} is invalid.")
    item.state = target
    setattr(item, _TIMESTAMPS[target], timezone.now())
    item.save(update_fields=["state", _TIMESTAMPS[target]])
    if target == OrderItem.State.READY:
        from dispatch.services import ensure_delivery_task
        ensure_delivery_task(item.id)
    return item


@transaction.atomic
def cancel_order_item(item_id, actor, reason):
    if not reason: raise ValidationError("A cancellation reason is required.")
    item = OrderItem.objects.select_for_update().select_related("order__tab__venue").get(pk=item_id)
    if actor.venue_id != item.order.tab.venue_id: raise PermissionDenied("Staff member does not belong to this venue.")
    if item.order.tab.status == Tab.Status.CLOSED: raise ValidationError("Cannot cancel an item on a closed tab.")
    if item.state == OrderItem.State.CANCELLED: return item
    if item.order.status == Order.Status.CONFIRMED and not actor.can_manage_finance:
        raise PermissionDenied("Only a manager can cancel a confirmed item.")
    before = {"state": item.state}
    item.state, item.cancelled_at = OrderItem.State.CANCELLED, timezone.now()
    item.save(update_fields=["state", "cancelled_at"])
    if item.order.status == Order.Status.CONFIRMED:
        shift = CashShift.objects.filter(venue=item.order.tab.venue, closed_at__isnull=True).first()
        Adjustment.objects.get_or_create(tab=item.order.tab, order_item=item, defaults={
            "amount_cents": -(item.unit_price_cents * item.quantity), "type": Adjustment.Type.REVERSAL,
            "reason": reason, "created_by": actor, "cash_shift": shift,
        })
        _audit(actor, "order_item.cancelled", item, reason=reason, before=before, after={"state": item.state})
    return item


@transaction.atomic
def record_payment(tab_id, actor, *, amount_cents, method, idempotency_key=None, status=Payment.Status.CONFIRMED):
    tab = Tab.objects.select_for_update().select_related("venue").get(pk=tab_id)
    if actor.venue_id != tab.venue_id: raise PermissionDenied("Staff member does not belong to this venue.")
    if tab.status == Tab.Status.CLOSED: raise ValidationError("Cannot receive a payment on a closed tab.")
    if amount_cents <= 0: raise ValidationError("Payment amount must be positive.")
    if method not in Payment.Method.values: raise ValidationError("Invalid payment method.")
    if status not in Payment.Status.values: raise ValidationError("Invalid payment status.")
    if status == Payment.Status.CONFIRMED and amount_cents > exposure_cents(tab):
        raise ValidationError("Payment cannot exceed the tab's open exposure.")
    if idempotency_key:
        prior = Payment.objects.filter(tab=tab, idempotency_key=idempotency_key).first()
        if prior:
            if prior.amount_cents != amount_cents or prior.method != method or prior.status != status:
                raise ValidationError("Idempotency key was already used with a different payment.")
            return prior
    shift = CashShift.objects.filter(venue=tab.venue, closed_at__isnull=True).first()
    now = timezone.now()
    try:
        payment = Payment.objects.create(tab=tab, cash_shift=shift, amount_cents=amount_cents, method=method,
            status=status, idempotency_key=idempotency_key or None, received_by=actor,
            confirmed_at=now if status == Payment.Status.CONFIRMED else None)
        if status == Payment.Status.CONFIRMED and tab.status == Tab.Status.REQUIRES_ACTION and exposure_cents(tab) < tab.operating_limit_cents:
            tab.status = Tab.Status.OPEN
            tab.save(update_fields=["status"])
        _audit(actor, "payment.recorded", payment, after={
            "amount_cents": payment.amount_cents,
            "method": payment.method,
            "status": payment.status,
            "exposure_cents": exposure_cents(tab),
        })
        return payment
    except IntegrityError:
        return Payment.objects.get(tab=tab, idempotency_key=idempotency_key)


@transaction.atomic
def create_adjustment(tab_id, actor, *, amount_cents, kind, reason):
    if not actor.can_manage_finance: raise PermissionDenied("Only a manager can adjust a ledger.")
    if not reason: raise ValidationError("An adjustment reason is required.")
    tab = Tab.objects.select_for_update().select_related("venue").get(pk=tab_id)
    if actor.venue_id != tab.venue_id: raise PermissionDenied("Staff member does not belong to this venue.")
    if tab.status == Tab.Status.CLOSED: raise ValidationError("Cannot adjust a closed tab.")
    if amount_cents == 0: raise ValidationError("Adjustment amount cannot be zero.")
    if kind not in Adjustment.Type.values: raise ValidationError("Invalid adjustment type.")
    shift = CashShift.objects.filter(venue=tab.venue, closed_at__isnull=True).first()
    adjustment = Adjustment.objects.create(tab=tab, cash_shift=shift, amount_cents=amount_cents, type=kind, reason=reason, created_by=actor)
    _audit(actor, "ledger.adjustment.created", adjustment, reason=reason, after={"amount_cents": amount_cents, "type": kind})
    return adjustment


@transaction.atomic
def close_tab(tab_id, actor, *, force=False, reason=""):
    tab = Tab.objects.select_for_update().select_related("venue").get(pk=tab_id)
    if actor.venue_id != tab.venue_id: raise PermissionDenied("Staff member does not belong to this venue.")
    if tab.status == Tab.Status.CLOSED: return tab
    if not actor.can_operate_cash: raise PermissionDenied("Only a cashier or manager can close a tab.")
    balance = exposure_cents(tab)
    if balance != 0:
        if not (force and actor.can_manage_finance and reason):
            raise ValidationError("Tab can only close with zero open exposure.")
        _audit(actor, "tab.force_closed", tab, reason=reason, before={"exposure_cents": balance}, after={"status": Tab.Status.CLOSED})
    tab.status, tab.closed_at = Tab.Status.CLOSED, timezone.now()
    tab.save(update_fields=["status", "closed_at"])
    if balance == 0:
        _audit(actor, "tab.closed", tab, after={"status": tab.status, "exposure_cents": 0})
    return tab
