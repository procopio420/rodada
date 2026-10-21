from django.db import migrations


def seed_enforce(apps, schema_editor):
    venue = apps.get_model("venue", "Venue")
    policy = apps.get_model("house_account", "VenueSpendingLimitPolicy")
    database = schema_editor.connection.alias
    for venue_id in venue.objects.using(database).values_list("pk", flat=True).iterator():
        policy.objects.using(database).get_or_create(venue_id=venue_id, defaults={"mode": "ENFORCE", "version": 1})


class Migration(migrations.Migration):
    dependencies = [("house_account", "0003_venuespendinglimitpolicy_spendinglimitpolicycommand")]
    operations = [migrations.RunPython(seed_enforce, migrations.RunPython.noop)]
