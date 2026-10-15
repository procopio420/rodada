"""Safety boundary shared by the native Android / browser test harness.

Importable without Django, so unsafe destinations fail before Django startup.
The allowlist is deliberately exact; a test-looking prefix is not isolation.
"""
import os

DATABASES = frozenset({"rodada_android_post_drop", "rodada_android_post_drop_link_cut"})
VENUE_SLUG = "android-post-drop-ci"
LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def require_disposable_database(config=None):
    if config is None:
        config = {
            "ENGINE": os.environ.get("DJANGO_DB_ENGINE", "django.db.backends.postgresql"),
            "NAME": os.environ.get("POSTGRES_DB"),
            "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        }
    if (
        config.get("ENGINE") != "django.db.backends.postgresql"
        or config.get("NAME") not in DATABASES
        or config.get("HOST") not in LOCAL_HOSTS
        or any(key in config.get("OPTIONS", {}) for key in ("service", "host", "hostaddr", "dbname", "database", "port"))
    ):
        raise RuntimeError("Cross-surface tests require an allowlisted local disposable PostgreSQL database")
    # libpq service files and hostaddr can override the apparently local host.
    if any(os.environ.get(key) for key in ("PGSERVICE", "PGSERVICEFILE", "PGHOSTADDR")):
        raise RuntimeError("Cross-surface tests forbid libpq destination overrides")
    return config["NAME"]


def require_connected_database(connection):
    expected = require_disposable_database(connection.settings_dict)
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database(), inet_server_addr()::text")
        database, address = cursor.fetchone()
    if database != expected or address not in LOCAL_HOSTS:
        raise RuntimeError("Connected database does not match the disposable local fixture")
    return database


def require_fixture_order(order, fixture):
    """Never reconcile a receipt against a foreign Venue or fixture generation."""
    if fixture.get("venue_slug") != VENUE_SLUG or order.tab.venue.slug != VENUE_SLUG:
        raise RuntimeError("Native order does not belong to the cross-surface fixture Venue")
    if str(order.tab.venue_id) != fixture.get("venue_id"):
        raise RuntimeError("Native order belongs to another fixture generation")
