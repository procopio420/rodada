from django.db import models


class Customer(models.Model):
    display_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=32, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_name", "id"]


class Relationship(models.Model):
    class Status(models.TextChoices):
        VISITOR = "VISITOR", "Visitor"
        KNOWN = "KNOWN", "Known"
        REGULAR = "REGULAR", "Regular"
        HOUSE = "HOUSE", "House"
        RESTRICTED = "RESTRICTED", "Restricted"

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="relationships")
    venue = models.ForeignKey("pos.Venue", on_delete=models.PROTECT, related_name="relationships")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.VISITOR)
    nickname = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["customer", "venue"], name="one_relationship_per_customer_venue")]


class VenueRelationshipPolicy(models.Model):
    venue = models.ForeignKey("pos.Venue", on_delete=models.PROTECT, related_name="relationship_policies")
    status = models.CharField(max_length=12, choices=Relationship.Status.choices)
    operating_limit_cents = models.PositiveIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["venue", "status"], name="one_policy_per_venue_status")]
