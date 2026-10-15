"""Explicit opt-in cleanup of disposable Web E2E data between independent tests."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "api"))
os.environ["DJANGO_SETTINGS_MODULE"] = "rodada_api.settings"
import django
django.setup()
from django.db import OperationalError, connection, transaction
from fixture_backend import seed

db = connection.settings_dict
if (os.environ.get("RODADA_E2E_POSTGRES") != "1" or os.environ.get("RODADA_E2E_RESET") != "1"
        or db["ENGINE"] != "django.db.backends.postgresql" or db["NAME"] != "rodada_web_e2e"
        or db["HOST"] not in ("127.0.0.1", "localhost")):
    raise RuntimeError("Refusing reset outside explicitly disposable local Web E2E")
for attempt in range(3):
    try:
        with transaction.atomic():
            names = sorted(n for n in connection.introspection.table_names() if n != "django_migrations")
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE " + ", ".join(connection.ops.quote_name(n) for n in names)
                               + " RESTART IDENTITY CASCADE")
            seed()
        break
    except OperationalError as error:
        # A previous page's in-flight read can overlap the next test's cleanup.
        # PostgreSQL rolls the entire cleanup back on 40P01; retry only that
        # disposable setup transaction, never a test or a product mutation.
        if getattr(error.__cause__, "sqlstate", None) != "40P01" or attempt == 2:
            raise
print("PASS: isolated E2E fixture restored; migrations preserved")
