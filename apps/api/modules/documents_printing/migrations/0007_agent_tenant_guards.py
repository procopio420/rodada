"""Protect tenant references even for bulk ORM/raw SQL writes on PostgreSQL."""

from django.db import migrations

FORWARD = r"""
CREATE FUNCTION printing_agent_tenant_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_TABLE_NAME = 'documents_printing_printagent' THEN
    IF TG_OP = 'UPDATE' AND OLD.paired_at IS NOT NULL AND
      (NEW.venue_id IS DISTINCT FROM OLD.venue_id OR NEW.device_id IS DISTINCT FROM OLD.device_id
       OR NEW.installation_id IS DISTINCT FROM OLD.installation_id OR NEW.paired_at IS NULL
       OR (OLD.revoked_at IS NOT NULL AND NEW.revoked_at IS DISTINCT FROM OLD.revoked_at)) THEN
      RAISE EXCEPTION 'Paired agent identity is immutable' USING ERRCODE = '23514';
    END IF;
    IF NEW.device_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM access_deviceregistration WHERE id=NEW.device_id AND venue_id=NEW.venue_id FOR SHARE
    ) THEN RAISE EXCEPTION 'Agent/device Venue mismatch' USING ERRCODE = '23514'; END IF;
  ELSIF TG_TABLE_NAME = 'documents_printing_agentprinterroute' THEN
    IF NOT EXISTS (
      SELECT 1 FROM documents_printing_printerendpoint e,
        documents_printing_discoveredprinter p JOIN documents_printing_printagent a ON a.id=p.agent_id
      WHERE e.id=NEW.endpoint_id AND p.id=NEW.printer_id AND e.venue_id=a.venue_id
        AND p.transport=NEW.transport FOR SHARE OF e, p, a
    ) THEN RAISE EXCEPTION 'Route Venue/transport mismatch' USING ERRCODE = '23514'; END IF;
  ELSIF TG_TABLE_NAME = 'documents_printing_discoveredprinter' THEN
    IF TG_OP='UPDATE' AND (NEW.agent_id IS DISTINCT FROM OLD.agent_id
      OR NEW.local_id IS DISTINCT FROM OLD.local_id OR NEW.transport IS DISTINCT FROM OLD.transport) THEN
      RAISE EXCEPTION 'Discovery identity is immutable' USING ERRCODE = '23514';
    END IF;
  ELSIF TG_TABLE_NAME = 'access_deviceregistration' THEN
    IF TG_OP='UPDATE' AND NEW.venue_id IS DISTINCT FROM OLD.venue_id AND EXISTS (
      SELECT 1 FROM documents_printing_printagent WHERE device_id=OLD.id
    ) THEN RAISE EXCEPTION 'Agent device Venue is immutable' USING ERRCODE = '23514'; END IF;
  ELSIF TG_TABLE_NAME = 'documents_printing_printerendpoint' THEN
    IF TG_OP='UPDATE' AND NEW.venue_id IS DISTINCT FROM OLD.venue_id AND EXISTS (
      SELECT 1 FROM documents_printing_agentprinterroute WHERE endpoint_id=OLD.id
    ) THEN RAISE EXCEPTION 'Routed endpoint Venue is immutable' USING ERRCODE = '23514'; END IF;
  ELSIF TG_TABLE_NAME = 'access_agentcredential' THEN
    IF NOT EXISTS (SELECT 1 FROM documents_printing_printagent WHERE id=NEW.agent_id
      AND venue_id IS NOT NULL AND paired_at IS NOT NULL AND revoked_at IS NULL)
      AND NEW.revoked_at IS NULL THEN
      RAISE EXCEPTION 'Credential requires paired agent' USING ERRCODE = '23514';
    END IF;
    IF TG_OP='UPDATE' AND (NEW.agent_id IS DISTINCT FROM OLD.agent_id
      OR NEW.token_hash IS DISTINCT FROM OLD.token_hash OR NEW.scope IS DISTINCT FROM OLD.scope
      OR NEW.expires_at IS DISTINCT FROM OLD.expires_at
      OR (OLD.revoked_at IS NOT NULL AND NEW.revoked_at IS DISTINCT FROM OLD.revoked_at)) THEN
      RAISE EXCEPTION 'Credential identity/revocation is immutable' USING ERRCODE = '23514';
    END IF;
  ELSIF TG_TABLE_NAME = 'documents_printing_printpairingrequest' THEN
    IF NEW.approved_venue_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM documents_printing_printagent WHERE id=NEW.agent_id AND venue_id=NEW.approved_venue_id
    ) THEN RAISE EXCEPTION 'Pairing approval Venue mismatch' USING ERRCODE = '23514'; END IF;
    IF TG_OP='UPDATE' AND (NEW.agent_id IS DISTINCT FROM OLD.agent_id
      OR NEW.code_hash IS DISTINCT FROM OLD.code_hash OR NEW.proof_hash IS DISTINCT FROM OLD.proof_hash
      OR NEW.expires_at IS DISTINCT FROM OLD.expires_at
      OR (OLD.consumed_at IS NOT NULL AND (NEW.consumed_at IS DISTINCT FROM OLD.consumed_at
        OR NEW.approved_by_id IS DISTINCT FROM OLD.approved_by_id
        OR NEW.approved_venue_id IS DISTINCT FROM OLD.approved_venue_id))) THEN
      RAISE EXCEPTION 'Pairing identity/consumption is immutable' USING ERRCODE = '23514';
    END IF;
  END IF;
  RETURN NEW;
END $$;
"""
TABLES = (
    "documents_printing_printagent",
    "documents_printing_agentprinterroute",
    "documents_printing_discoveredprinter",
    "access_deviceregistration",
    "documents_printing_printerendpoint",
    "access_agentcredential",
    "documents_printing_printpairingrequest",
)


def install(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(FORWARD)
    for table in TABLES:
        schema_editor.execute(
            f"CREATE TRIGGER printing_tenant_guard BEFORE INSERT OR UPDATE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION printing_agent_tenant_guard()"
        )


def uninstall(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    for table in TABLES:
        schema_editor.execute(f"DROP TRIGGER printing_tenant_guard ON {table}")
    schema_editor.execute("DROP FUNCTION printing_agent_tenant_guard()")


class Migration(migrations.Migration):
    dependencies = [
        ("documents_printing", "0006_printagent_discoveredprinter_printpairingrequest_and_more"),
        ("access", "0005_agentcredential_agent_and_more"),
    ]
    operations = [migrations.RunPython(install, uninstall)]
