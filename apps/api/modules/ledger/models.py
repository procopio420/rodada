import uuid

from django.db import models

from modules.access.models import StaffMember
from modules.ordering.models import OrderItem, Tab


class Charge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tab = models.ForeignKey(Tab, on_delete=models.PROTECT, related_name="charges")
    order_item = models.OneToOneField(OrderItem, on_delete=models.PROTECT, related_name="charge")
    amount_cents = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class PaymentMethod(models.TextChoices):
    CASH = "CASH", "Cash"
    CARD = "CARD", "Card"
    PIX = "PIX", "Pix"
    OTHER = "OTHER", "Other"


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tab = models.ForeignKey(Tab, on_delete=models.PROTECT, related_name="payments")
    amount_cents = models.PositiveIntegerField()
    method = models.CharField(max_length=12, choices=PaymentMethod.choices)
    idempotency_key = models.CharField(max_length=120)
    received_by = models.ForeignKey(StaffMember, on_delete=models.PROTECT, related_name="payments_received")
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("tab", "idempotency_key"), name="ledger_payment_tab_key_unique")]
