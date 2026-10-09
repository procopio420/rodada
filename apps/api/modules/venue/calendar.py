from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from django.utils import timezone


def business_date(venue, instant=None):
    local = (instant or timezone.now()).astimezone(ZoneInfo(venue.timezone))
    return (local - timedelta(hours=venue.business_day_cutoff_hour)).date()


def business_boundary(venue, day):
    return datetime.combine(day, time(venue.business_day_cutoff_hour), tzinfo=ZoneInfo(venue.timezone))
