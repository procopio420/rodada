from django.db import models


class Charge(models.Model):
    tab = models.ForeignKey("pos.Tab", on_delete=models.PROTECT, related_name="charges")
    order_item = models.OneToOneField("pos.OrderItem", on_delete=models.PROTECT, related_name="charge")
    amount_cents = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class Payment(models.Model):
    class Method(models.TextChoices): PIX = "PIX", "Pix"; CARD = "CARD", "Card"; CASH = "CASH", "Cash"; OTHER = "OTHER", "Other"
    class Status(models.TextChoices): PENDING = "PENDING", "Pending"; CONFIRMED = "CONFIRMED", "Confirmed"; FAILED = "FAILED", "Failed"; REVERSED = "REVERSED", "Reversed"
    tab = models.ForeignKey("pos.Tab", on_delete=models.PROTECT, related_name="payments")
    cash_shift = models.ForeignKey("cash.CashShift", null=True, blank=True, on_delete=models.PROTECT, related_name="payments")
    amount_cents = models.PositiveIntegerField()
    method = models.CharField(max_length=8, choices=Method.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.CONFIRMED)
    idempotency_key = models.CharField(max_length=100, null=True, blank=True)
    received_by = models.ForeignKey("pos.StaffMember", null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["tab", "idempotency_key"], condition=models.Q(idempotency_key__isnull=False), name="unique_payment_command_per_tab")]


class PaymentIntent(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        FAILED = "FAILED", "Failed"
        CANCELED = "CANCELED", "Canceled"

    tab = models.ForeignKey("pos.Tab", on_delete=models.PROTECT, related_name="payment_intents")
    amount_cents = models.PositiveIntegerField()
    method = models.CharField(max_length=8, choices=Payment.Method.choices, default=Payment.Method.CARD)
    provider = models.CharField(max_length=32)
    provider_reference = models.CharField(max_length=120, unique=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    idempotency_key = models.CharField(max_length=100, unique=True)
    payment = models.OneToOneField(Payment, null=True, blank=True, on_delete=models.SET_NULL, related_name="intent")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)


class Adjustment(models.Model):
    class Type(models.TextChoices): COURTESY = "COURTESY", "Courtesy"; CORRECTION = "CORRECTION", "Correction"; REVERSAL = "REVERSAL", "Reversal"
    tab = models.ForeignKey("pos.Tab", on_delete=models.PROTECT, related_name="adjustments")
    order_item = models.OneToOneField("pos.OrderItem", null=True, blank=True, on_delete=models.PROTECT, related_name="reversal_adjustment")
    cash_shift = models.ForeignKey("cash.CashShift", null=True, blank=True, on_delete=models.PROTECT, related_name="adjustments")
    amount_cents = models.IntegerField(help_text="Signed effect on exposure")
    type = models.CharField(max_length=12, choices=Type.choices)
    reason = models.TextField()
    created_by = models.ForeignKey("pos.StaffMember", null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
