from django.db import models


class VenueStream(models.Model):
    venue = models.OneToOneField("venue.Venue", primary_key=True, on_delete=models.CASCADE)
    sequence = models.PositiveBigIntegerField(default=0)


class OutboxEvent(models.Model):
    venue = models.ForeignKey("venue.Venue", on_delete=models.CASCADE)
    sequence = models.PositiveBigIntegerField()
    event_type = models.CharField(max_length=120)
    aggregate_type = models.CharField(max_length=80)
    aggregate_id = models.CharField(max_length=80)
    tab_id = models.UUIDField(null=True)
    payload = models.JSONField(default=dict)
    occurred_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["venue", "sequence"], name="realtime_venue_sequence")
        ]
        indexes = [
            models.Index(fields=["venue", "sequence"]),
            models.Index(fields=["published_at", "id"]),
        ]

    @property
    def cursor(self):
        return f"{self.venue_id}:{self.sequence}"

    def envelope(self):
        return {
            "schema_version": 1,
            "id": self.cursor,
            "venue_id": str(self.venue_id),
            "type": self.event_type,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "version": self.sequence,
            "occurred_at": self.occurred_at.isoformat(),
            "payload": self.payload,
        }
