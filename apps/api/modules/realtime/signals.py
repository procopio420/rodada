"""Bridge named existing canonical audit facts; never copy audit/financial payloads."""

from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver

from modules.audit.models import AuditEvent

from .services import emit_event

PREFIXES = (
    "tab.",
    "table.",
    "table_occupancy.",
    "zone.",
    "guest_tab.",
    "order_item.",
    "dispatch.",
    "payment.",
    "charge.",
    "replacement.",
    "product.availability_",
    "guest_session.",
    "cash.",
    "catalog.product_created",
    "catalog.product_edited",
    "catalog.icon_published",
    "catalog.icon_uploaded",
    "catalog.icon_removed",
)
MODELS = {
    "Tab": "ordering.Tab",
    "OrderItem": "ordering.OrderItem",
    "Order": "ordering.Order",
    "Payment": "ledger.Payment",
    "Refund": "ledger.Refund",
    "LedgerAdjustment": "ledger.LedgerAdjustment",
    "DispatchTask": "dispatch.DispatchTask",
}


@receiver(post_save, sender=AuditEvent)
def audit_fact(sender, instance, created, **kwargs):
    if not created or not instance.event_type.startswith(PREFIXES):
        return
    tab_id = None
    model = MODELS.get(instance.entity_type)
    if model and instance.entity_id:
        obj = apps.get_model(model).objects.filter(pk=instance.entity_id).first()
        if obj:
            if instance.entity_type == "Tab":
                tab_id = obj.id
            elif instance.entity_type == "OrderItem":
                tab_id = obj.order.tab_id
            elif instance.entity_type == "Refund":
                tab_id = obj.payment.tab_id
            elif instance.entity_type == "DispatchTask":
                tab_id = obj.order_item.order.tab_id if obj.order_item_id else None
            else:
                tab_id = obj.tab_id
    emit_event(
        venue_id=instance.venue_id,
        event_type=instance.event_type,
        aggregate_type=instance.entity_type,
        aggregate_id=instance.entity_id,
        tab_id=tab_id,
    )
