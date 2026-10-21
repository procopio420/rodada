import uuid

from django.db import models


class RelationshipKind(models.TextChoices):
    VISITOR = "VISITOR", "Visitante"
    KNOWN = "KNOWN", "Conhecido"
    REGULAR = "REGULAR", "Regular"
    HOUSE = "HOUSE", "Da casa"
    RESTRICTED = "RESTRICTED", "Restrito"


DEMO_LIMITS = {"VISITOR": 3000, "KNOWN": 8000, "REGULAR": 20000, "HOUSE": 50000, "RESTRICTED": 0}


class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    display_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40, blank=True)
    notes = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Relationship(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey("venue.Venue", on_delete=models.PROTECT)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    kind = models.CharField(max_length=16, choices=RelationshipKind.choices, default="KNOWN")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["venue", "customer"], name="house_relationship_unique")
        ]


class VenueRelationshipPolicy(models.Model):
    venue = models.ForeignKey("venue.Venue", on_delete=models.PROTECT)
    kind = models.CharField(max_length=16, choices=RelationshipKind.choices)
    limit_cents = models.PositiveIntegerField()
    version = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["venue", "kind"], name="house_policy_unique")
        ]


class LimitOverride(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tab = models.ForeignKey(
        "ordering.Tab", on_delete=models.PROTECT, related_name="limit_overrides"
    )
    previous_limit_cents = models.PositiveIntegerField()
    limit_cents = models.PositiveIntegerField()
    actor = models.ForeignKey("access.StaffMember", on_delete=models.PROTECT)
    reason = models.CharField(max_length=240)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    idempotency_key = models.CharField(max_length=120)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tab", "idempotency_key"], name="house_override_idempotent"
            )
        ]
        ordering = ["created_at", "id"]


class SpendingLimitMode(models.TextChoices):
    ENFORCE = "ENFORCE", "Bloquear pedidos"
    WARN_ONLY = "WARN_ONLY", "Só alertar"


class VenueSpendingLimitPolicy(models.Model):
    venue = models.OneToOneField("venue.Venue", on_delete=models.PROTECT, primary_key=True)
    mode = models.CharField(max_length=16, choices=SpendingLimitMode.choices, default=SpendingLimitMode.ENFORCE)
    version = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(mode__in=SpendingLimitMode.values), name="house_spending_mode_valid"),
            models.CheckConstraint(condition=models.Q(version__gte=1), name="house_spending_version_positive"),
        ]


class SpendingLimitPolicyCommand(models.Model):
    """Immutable command receipt; replay must return the original policy version."""
    venue = models.ForeignKey("venue.Venue", on_delete=models.PROTECT)
    idempotency_key = models.CharField(max_length=120)
    request = models.JSONField()
    response = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["venue", "idempotency_key"], name="house_spending_command_unique")]
