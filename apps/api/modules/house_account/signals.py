from django.db.models.signals import post_save
from django.dispatch import receiver

from modules.venue.models import Venue

from .models import VenueSpendingLimitPolicy


@receiver(post_save, sender=Venue, dispatch_uid="house_account.bootstrap_spending_policy")
def bootstrap_spending_policy(sender, instance, created, raw=False, using="default", **kwargs):
    if created and not raw:
        VenueSpendingLimitPolicy.objects.using(using).get_or_create(venue_id=instance.pk)
