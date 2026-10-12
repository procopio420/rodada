"""Map only an existing pilot; do not create or rename a Venue or alter DNS."""

from django.db import migrations


def seed_existing_pilot(apps, schema_editor):
    Venue = apps.get_model("venue", "Venue")
    VenueDomain = apps.get_model("venue", "VenueDomain")
    AuditEvent = apps.get_model("audit", "AuditEvent")
    database = schema_editor.connection.alias
    venue = Venue.objects.using(database).filter(slug="bar-do-aderlan").first()
    if venue is None:
        return
    domain, created = VenueDomain.objects.using(database).get_or_create(
        hostname="bardoaderlan.rodada.ai",
        defaults={
            "venue_id": venue.pk,
            "is_active": True,
            "is_verified": True,
            "is_primary": not VenueDomain.objects.using(database)
            .filter(venue_id=venue.pk, is_primary=True)
            .exists(),
        },
    )
    if domain.venue_id != venue.pk:
        raise RuntimeError("Pilot hostname belongs to a different Venue")
    if created:
        AuditEvent.objects.using(database).create(
            venue_id=venue.pk,
            event_type="venue.domain_configured",
            entity_type="VenueDomain",
            entity_id=str(domain.pk),
            reason="Spec 025 existing pilot mapping; platform-owned alias",
            metadata={
                "before": [],
                "after": {
                    "hostname": domain.hostname,
                    "is_primary": domain.is_primary,
                    "is_active": True,
                    "is_verified": True,
                },
            },
        )


class Migration(migrations.Migration):
    dependencies = [("venue", "0008_venuedomain"), ("audit", "0001_initial")]
    # Rollback preserves provisioned identity and its audit trail. Disable via lifecycle service.
    operations = [migrations.RunPython(seed_existing_pilot, migrations.RunPython.noop)]
