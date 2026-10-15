"""Safety boundary shared by the native Android / browser test harness.

Importable without Django, so unsafe destinations fail before Django startup.
The allowlist is deliberately exact; a test-looking prefix is not isolation.
"""
import ipaddress
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
        cursor.execute("SELECT current_database(), host(inet_server_addr())")
        database, address = cursor.fetchone()
    # A host-run job reaches its disposable Docker service through loopback,
    # while PostgreSQL observes the service's bridge IP. Accept only that exact
    # independently inspected container address, never an arbitrary private IP.
    container_address = os.environ.get("RODADA_TEST_DB_CONTAINER_ADDRESS")
    allowed_addresses = set(LOCAL_HOSTS)
    if container_address:
        parsed = ipaddress.ip_address(container_address)
        if os.environ.get("CI") != "true" or not parsed.is_private or parsed.is_unspecified:
            raise RuntimeError("Container database address requires an explicit private CI service identity")
        allowed_addresses.add(str(parsed))
    if database != expected or address not in allowed_addresses:
        raise RuntimeError(
            f"Connected database does not match the disposable local fixture: database={database!r}, "
            f"server={address!r}, expected_database={expected!r}, expected_servers={sorted(allowed_addresses)!r}"
        )
    return database


def require_fixture_order(order, fixture):
    """Never reconcile a receipt against a foreign Venue or fixture generation."""
    if fixture.get("venue_slug") != VENUE_SLUG or order.tab.venue.slug != VENUE_SLUG:
        raise RuntimeError("Native order does not belong to the cross-surface fixture Venue")
    if str(order.tab.venue_id) != fixture.get("venue_id"):
        raise RuntimeError("Native order belongs to another fixture generation")
