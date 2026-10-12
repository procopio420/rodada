"""PostgreSQL defense in depth for privileged ORM/SQL domain changes."""

from django.db import migrations

SQL = """
CREATE FUNCTION rodada_venue_domain_lifecycle() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Disable VenueDomain instead of deleting its identity';
    END IF;
    IF TG_OP = 'UPDATE' AND (OLD.hostname <> NEW.hostname OR OLD.venue_id <> NEW.venue_id) THEN
        RAISE EXCEPTION 'VenueDomain identity is immutable; provision a new alias';
    END IF;
    INSERT INTO audit_auditevent
        (id, venue_id, event_type, entity_type, entity_id, reason, metadata, occurred_at)
    VALUES
        (gen_random_uuid(), NEW.venue_id, 'venue.domain_database_changed', 'VenueDomain',
         NEW.id::text, 'Database domain lifecycle',
         jsonb_build_object('operation', TG_OP,
             'before', CASE WHEN TG_OP = 'UPDATE' THEN to_jsonb(OLD) ELSE NULL END,
             'after', to_jsonb(NEW)), CURRENT_TIMESTAMP);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER rodada_venue_domain_lifecycle_trigger
    BEFORE INSERT OR UPDATE OR DELETE ON venue_venuedomain
    FOR EACH ROW EXECUTE FUNCTION rodada_venue_domain_lifecycle();
"""


def install(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(SQL)


def uninstall(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            "DROP TRIGGER rodada_venue_domain_lifecycle_trigger ON venue_venuedomain"
        )
        schema_editor.execute("DROP FUNCTION rodada_venue_domain_lifecycle()")


class Migration(migrations.Migration):
    dependencies = [("venue", "0009_pilot_venue_domain")]
    operations = [migrations.RunPython(install, uninstall)]
