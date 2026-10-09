import uuid

from django.db import models


class Venue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=80, unique=True)
    timezone = models.CharField(max_length=64, default="America/Sao_Paulo")
    business_day_cutoff_hour = models.PositiveSmallIntegerField(default=0, db_default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)
        constraints = [models.CheckConstraint(condition=models.Q(business_day_cutoff_hour__lte=23), name="venue_cutoff_valid_hour")]

    def __str__(self) -> str:
        return self.name
