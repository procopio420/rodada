"""Extend immutable identity guards to S2 proof and credential delivery metadata."""
from importlib import import_module

from django.db import migrations

BASE = import_module("modules.documents_printing.migrations.0007_agent_tenant_guards").FORWARD
UPDATED = BASE.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1).replace(
    "IF TG_TABLE_NAME = 'documents_printing_printagent' THEN",
    """IF TG_TABLE_NAME = 'documents_printing_printagent' THEN
    IF TG_OP='UPDATE' AND OLD.installation_proof_hash <> '' AND
       NEW.installation_proof_hash IS DISTINCT FROM OLD.installation_proof_hash THEN
      RAISE EXCEPTION 'Installation proof is immutable' USING ERRCODE = '23514';
    END IF;""",
).replace(
    "ELSIF TG_TABLE_NAME = 'documents_printing_printpairingrequest' THEN",
    """ELSIF TG_TABLE_NAME = 'documents_printing_printpairingrequest' THEN
    IF NEW.credential_id IS NOT NULL AND (NEW.consumed_at IS NULL OR NOT EXISTS (
      SELECT 1 FROM access_agentcredential WHERE id=NEW.credential_id AND agent_id=NEW.agent_id
    )) THEN RAISE EXCEPTION 'Pairing credential identity mismatch' USING ERRCODE = '23514'; END IF;
    IF NEW.activated_at IS NOT NULL AND (NEW.consumed_at IS NULL OR NEW.credential_id IS NULL) THEN
      RAISE EXCEPTION 'Activation requires approved credential' USING ERRCODE = '23514';
    END IF;
    IF TG_OP='UPDATE' AND ((OLD.credential_id IS NOT NULL AND
      NEW.credential_id IS DISTINCT FROM OLD.credential_id) OR
      (OLD.activated_at IS NOT NULL AND NEW.activated_at IS DISTINCT FROM OLD.activated_at)) THEN
      RAISE EXCEPTION 'Pairing delivery metadata is immutable' USING ERRCODE = '23514';
    END IF;""",
)


def forward(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(UPDATED)


def backward(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(BASE.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1))


class Migration(migrations.Migration):
    dependencies = [("documents_printing", "0010_printagent_installation_proof_hash")]
    operations = [migrations.RunPython(forward, backward)]
