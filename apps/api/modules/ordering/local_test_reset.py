"""One-off local test cleanup: retains financial facts, never fabricates payments."""
from django.db import transaction
from django.utils import timezone
from modules.audit.services import record_audit_event
from modules.ledger.models import Payment, AdjustmentKind
from modules.ledger.pricing import (
    write_fact, get_policy, components, net_consumption, allocate, assert_settleable,
)
from modules.ledger.services import exposure_cents, close_tab
from modules.ordering.models import Tab, OrderItem
from modules.dispatch.models import DispatchTask
from modules.tab_operations.services import payment_blocker

REASON = "LOCAL_TEST_RESET"


@transaction.atomic
def reset_test_tabs(*, tab_ids, actor):
    tabs = list(Tab.objects.select_for_update().filter(pk__in=tab_ids, venue_id=actor.venue_id))
    if len(tabs) != len(set(tab_ids)):
        raise ValueError("Manifesto contém comanda inexistente ou de outro Venue.")
    payments_before = list(Payment.objects.filter(tab_id__in=tab_ids).values())
    results = []
    for tab in tabs:
        before = tab.state
        amount = exposure_cents(tab)
        if tab.state not in ("CLOSED", "CANCELLED"):
            if payment_blocker(tab, confirmed=False):
                raise ValueError("Pagamento ambíguo impede limpeza; revisar antes.")
            assert_settleable(tab)
            bases = {key: net_consumption(row) for key, row in components(tab).items()}
            if amount < 0 or amount > sum(bases.values()):
                raise ValueError("Saldo não pode ser dispensado sem revisão financeira.")
            key = f"local-test-reset:{tab.pk}"
            if amount:
                write_fact(tab, {
                    "kind": AdjustmentKind.COURTESY, "scope": "TAB", "calculation_type": "FIXED",
                    "requested_value": amount, "basis_cents": sum(bases.values()),
                    "amount_cents": -amount, "allocations": allocate(-amount, bases),
                }, {"idempotency_key": key, "reason_code": REASON,
                    "reason_text": "Encerramento de teste local solicitado pelo desenvolvedor; sem recebimento."},
                    actor, get_policy(actor.venue_id))
            close_tab(tab_id=tab.pk, actor=actor)
        items = list(OrderItem.objects.select_for_update().filter(order__tab=tab).exclude(state__in=("DELIVERED", "CANCELLED")))
        for item in items:
            old = item.state
            item.state = "CANCELLED"
            item.cancelled_at = timezone.now()
            item.save(update_fields=["state", "cancelled_at"])
            record_audit_event(actor=actor, event_type="demo.order_item_archived", entity_type="OrderItem",
                               entity_id=str(item.pk), reason=REASON, metadata={"before":old,"after":"CANCELLED","tab_id":str(tab.pk)})
        tasks = DispatchTask.objects.select_for_update().filter(venue_id=actor.venue_id, order_item__order__tab=tab).exclude(state__in=("DONE", "CANCELLED"))
        for task in tasks:
            old = task.state
            task.state = "CANCELLED"
            task.save(update_fields=["state", "updated_at"])
            record_audit_event(actor=actor,event_type="demo.task_archived",entity_type="DispatchTask",
                               entity_id=str(task.pk),reason=REASON,metadata={"before":old,"after":"CANCELLED"})
        tab.guest_sessions.filter(revoked_at__isnull=True).update(revoked_at=timezone.now(),revoked_reason=REASON)
        record_audit_event(actor=actor,event_type="demo.tab_reset",entity_type="Tab",entity_id=str(tab.pk),reason=REASON,
                           metadata={"before":before,"after":Tab.objects.get(pk=tab.pk).state,"waived_cents":amount,"items_archived":len(items)})
        results.append({"id":str(tab.pk),"waived_cents":amount,"items_archived":len(items)})
    assert payments_before == list(Payment.objects.filter(tab_id__in=tab_ids).values()), "Pagamentos foram alterados"
    return results
