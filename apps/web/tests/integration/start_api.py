"""Run the real API with explicit test-only fixtures in an isolated database.

SQLite is disposable locally; CI provisions a dedicated PostgreSQL service/database.
Never points at or seeds a developer's ordinary database by default.
"""
import os
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "api"))
os.environ["DJANGO_SETTINGS_MODULE"] = "rodada_api.settings"
os.environ["RODADA_BFF_HOST_SECRET"] = "rodada-integration-local-only"

from django.conf import settings

with tempfile.TemporaryDirectory(prefix="rodada-web-e2e-") as temporary:
    if os.environ.get("RODADA_E2E_POSTGRES") != "1":
        settings.DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": str(Path(temporary) / "test.sqlite3"), "OPTIONS": {"timeout": 20, "transaction_mode": "IMMEDIATE"}}}
    else:
        # Explicit opt-in requires the dedicated CI database, never ordinary rodada.
        if settings.DATABASES["default"]["NAME"] != "rodada_web_e2e":
            raise RuntimeError("Real Web tests require dedicated database rodada_web_e2e")
    settings.RODADA_AGENT_PAIRING_SECRET = "synthetic-web-e2e-pairing-key-only-028"
    settings.DEBUG = False
    settings.ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
    if os.environ.get("RODADA_E2E_ANDROID") == "1":
        settings.ALLOWED_HOSTS.append("10.0.2.2")

    import django
    django.setup()
    if os.environ.get("RODADA_E2E_MENU") == "1" and os.environ.get("RODADA_E2E_POSTGRES") == "1":
        # The ordinary BFF suite has populated this disposable database already.
        # Only the explicit canonical-menu run may reset it, and never outside
        # the isolated loopback PostgreSQL database used by Web E2E.
        database = settings.DATABASES["default"]
        if (database["ENGINE"] != "django.db.backends.postgresql"
                or database["NAME"] != "rodada_web_e2e"
                or database["HOST"] not in ("127.0.0.1", "localhost")):
            raise RuntimeError("Refusing to reset any non-disposable menu database")
        from django.core.management import call_command
        from e2e_db_guard import e2e_database_guard, retry_transient_reset
        with e2e_database_guard(exclusive=True):
            retry_transient_reset(lambda: call_command("flush", interactive=False, verbosity=0))
    from seed_api import seed_api
    seed_api()
    import threading
    import time
    import uvicorn
    from django.db import close_old_connections, OperationalError
    from modules.realtime.services import dispatch_pending
    from e2e_db_guard import e2e_database_guard

    def publish():
        while True:
            close_old_connections()
            try:
                # In PostgreSQL E2E, the per-file TRUNCATE/seed must never
                # overlap this publisher's queries/transactions.
                with e2e_database_guard(exclusive=False):
                    dispatch_pending()
            except OperationalError:
                # SQLite's single writer may be occupied by a test command.
                # The durable outbox remains pending and retries on the next pass.
                pass
            finally:
                close_old_connections()
            time.sleep(0.5)

    threading.Thread(target=publish, daemon=True).start()
    uvicorn.run("rodada_api.asgi:application", host="127.0.0.1", port=int(os.environ.get("RODADA_E2E_API_PORT", "8100")), log_level="warning")
