"""Register the existing Aderlan pilot hostname without creating or renaming a Venue."""
from django.db import migrations


def provision_pilot(apps, schema_editor):
    Venue = apps.get_model("venue", "Venue")
    VenueDomain = apps.get_model("venue", "VenueDomain")
    db = schema_editor.connection.alias
    venue = Venue.objects.using(db).filter(slug="bar-do-aderlan").first()
    if venue is None:
        # Other installations need not contain the demo pilot.
        return
    hostname = "bardoaderlan.rodada.bar"
    existing = VenueDomain.objects.using(db).filter(hostname=hostname).first()
    if existing is not None:
        if existing.venue_id != venue.pk:
            raise RuntimeError("Pilot hostname already belongs to another Venue")
        # Keep pre-existing flags unchanged, including manual suspensions.
    else:
        VenueDomain.objects.using(db).create(venue_id=venue.pk, hostname=hostname, is_active=True, is_verified=True)


class Migration(migrations.Migration):
    dependencies = [("venue", "0008_venue_domain")]
    operations = [migrations.RunPython(provision_pilot, migrations.RunPython.noop)]
