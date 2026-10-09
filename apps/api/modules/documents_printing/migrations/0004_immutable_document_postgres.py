# ruff: noqa: RUF012
"""Protect canonical receipt history even from bulk SQL on PostgreSQL."""

from django.db import migrations


def install(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute("""
        CREATE FUNCTION printing_document_immutable() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Receipt documents are immutable';
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER printing_document_immutable_trigger
        BEFORE UPDATE OR DELETE ON documents_printing_receiptdocument
        FOR EACH ROW EXECUTE FUNCTION printing_document_immutable();
    """)


def uninstall(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            "DROP TRIGGER IF EXISTS printing_document_immutable_trigger ON documents_printing_receiptdocument; DROP FUNCTION IF EXISTS printing_document_immutable();"
        )


class Migration(migrations.Migration):
    dependencies = [("documents_printing", "0003_receiptdocument_created_guest_session_and_more")]
    operations = [migrations.RunPython(install, uninstall)]
