"""Preserve tenant/transport ownership for additive executable attempts."""

import importlib
from typing import ClassVar

from django.db import migrations


def route_guard(schema_editor, forward):
    source = importlib.import_module(
        "modules.documents_printing.migrations.0011_pairing_identity_guards"
    ).UPDATED
    if forward:
        source = source.replace(
            "AND p.transport=NEW.transport FOR SHARE",
            "AND (p.transport=NEW.transport OR (p.transport='WINDOWS_DRIVER' AND NEW.transport='WINDOWS_RAW')) FOR SHARE",
        )
    schema_editor.execute(source.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1))


def install(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    route_guard(schema_editor, True)
    schema_editor.execute("""
    CREATE FUNCTION printing_attempt_owner_guard() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF TG_OP='UPDATE' AND OLD.agent_id IS NOT NULL AND
        (NEW.agent_id IS DISTINCT FROM OLD.agent_id OR NEW.route_id IS DISTINCT FROM OLD.route_id
         OR NEW.route_version IS DISTINCT FROM OLD.route_version OR NEW.job_id IS DISTINCT FROM OLD.job_id
         OR NEW.token IS DISTINCT FROM OLD.token) THEN
        RAISE EXCEPTION 'Attempt owner is immutable' USING ERRCODE='23514';
      END IF;
      IF NEW.agent_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM documents_printing_agentprinterroute r
        JOIN documents_printing_discoveredprinter p ON p.id=r.printer_id
        JOIN documents_printing_printjob j ON j.endpoint_id=r.endpoint_id
        JOIN documents_printing_receiptdocument d ON d.id=j.document_id
        JOIN documents_printing_printagent a ON a.id=p.agent_id
        WHERE r.id=NEW.route_id AND j.id=NEW.job_id AND a.id=NEW.agent_id
          AND d.venue_id=a.venue_id
      ) THEN RAISE EXCEPTION 'Attempt route/agent/job mismatch' USING ERRCODE='23514'; END IF;
      IF (NEW.agent_id IS NULL) <> (NEW.route_id IS NULL) OR
         (NEW.agent_id IS NULL) <> (NEW.route_version IS NULL) THEN
        RAISE EXCEPTION 'Incomplete attempt owner' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER printing_attempt_owner BEFORE INSERT OR UPDATE ON documents_printing_printattempt
      FOR EACH ROW EXECUTE FUNCTION printing_attempt_owner_guard();
    """)


def uninstall(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute("DROP TRIGGER printing_attempt_owner ON documents_printing_printattempt")
    schema_editor.execute("DROP FUNCTION printing_attempt_owner_guard()")
    route_guard(schema_editor, False)


class Migration(migrations.Migration):
    dependencies: ClassVar = [
        ("documents_printing", "0012_agentprinterroute_raw_escpos_verified_and_more")
    ]
    operations: ClassVar = [migrations.RunPython(install, uninstall)]
