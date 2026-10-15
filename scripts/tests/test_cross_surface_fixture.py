"""Safety regressions, not evidence of Android/browser execution."""
import os
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from cross_surface_fixture import (
    require_connected_database,
    require_disposable_database,
    require_fixture_order,
)


class CrossSurfaceFixtureTests(unittest.TestCase):
    def test_exact_database_and_loopback_required(self):
        for database in ("rodada_android_post_drop", "rodada_android_post_drop_link_cut"):
            with self.subTest(database=database), patch.dict(os.environ, {}, clear=True):
                self.assertEqual(require_disposable_database({
                    "NAME": database, "HOST": "127.0.0.1", "ENGINE": "django.db.backends.postgresql",
                }), database)

    def test_unsafe_targets_rejected_before_django_or_any_connection(self):
        for script in ("verify-android-live-post-drop.py", "verify-android-web-cross-surface.py"):
            for override in (
                {}, {"POSTGRES_DB": "rodada"},
                {"POSTGRES_DB": "rodada_android_post_drop_production"},
                {"POSTGRES_DB": "rodada_android_post_drop", "POSTGRES_HOST": "remote.example"},
                {"POSTGRES_DB": "rodada_android_post_drop", "DJANGO_DB_ENGINE": "django.db.backends.sqlite3"},
                {"POSTGRES_DB": "rodada_android_post_drop", "PGSERVICE": "production"},
                {"POSTGRES_DB": "rodada_android_post_drop", "PGHOSTADDR": "192.0.2.1"},
            ):
                with self.subTest(script=script, override=override):
                    result = subprocess.run(
                        [sys.executable, "-S", str(SCRIPTS / script), "prepare"],
                        env={"PATH": os.environ.get("PATH", ""), **override},
                        capture_output=True, text=True, check=False,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Cross-surface tests", result.stderr)
                    self.assertNotIn("No module named 'django'", result.stderr)

    def test_wrong_venue_or_generation_rejected(self):
        order = SimpleNamespace(tab=SimpleNamespace(venue_id="venue-a", venue=SimpleNamespace(slug="android-post-drop-ci")))
        require_fixture_order(order, {"venue_slug": "android-post-drop-ci", "venue_id": "venue-a"})
        for fixture in ({"venue_slug": "real-bar"}, {"venue_slug": "android-post-drop-ci", "venue_id": "venue-b"}):
            with self.subTest(fixture=fixture), self.assertRaises(RuntimeError):
                require_fixture_order(order, fixture)

    def test_effective_destination_checked_before_opening_cursor(self):
        connection = MagicMock(settings_dict={
            "NAME": "rodada_android_post_drop", "HOST": "127.0.0.1",
            "ENGINE": "django.db.backends.postgresql", "OPTIONS": {"host": "remote.example"},
        })
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(RuntimeError):
            require_connected_database(connection)
        connection.cursor.assert_not_called()

    def test_connected_identity_must_match_before_orm_access(self):
        connection = MagicMock(settings_dict={
            "NAME": "rodada_android_post_drop", "HOST": "127.0.0.1",
            "ENGINE": "django.db.backends.postgresql",
        })
        cursor = connection.cursor.return_value.__enter__.return_value
        with patch.dict(os.environ, {}, clear=True):
            for identity in (("rodada", "127.0.0.1"), ("rodada_android_post_drop", "192.0.2.1")):
                cursor.fetchone.return_value = identity
                with self.subTest(identity=identity), self.assertRaises(RuntimeError):
                    require_connected_database(connection)
            cursor.fetchone.return_value = ("rodada_android_post_drop", "127.0.0.1")
            self.assertEqual(require_connected_database(connection), "rodada_android_post_drop")
            cursor.execute.assert_called_with("SELECT current_database(), host(inet_server_addr())")

    def test_exact_ci_container_address_allowed_but_another_private_server_denied(self):
        connection = MagicMock(settings_dict={
            "NAME": "rodada_android_post_drop", "HOST": "127.0.0.1",
            "ENGINE": "django.db.backends.postgresql",
        })
        cursor = connection.cursor.return_value.__enter__.return_value
        env = {"CI": "true", "RODADA_TEST_DB_CONTAINER_ADDRESS": "172.18.0.2"}
        with patch.dict(os.environ, env, clear=True):
            cursor.fetchone.return_value = ("rodada_android_post_drop", "172.18.0.2")
            self.assertEqual(require_connected_database(connection), "rodada_android_post_drop")
            cursor.fetchone.return_value = ("rodada_android_post_drop", "172.18.0.3")
            with self.assertRaises(RuntimeError):
                require_connected_database(connection)
        with (
            patch.dict(os.environ, {"RODADA_TEST_DB_CONTAINER_ADDRESS": "172.18.0.2"}, clear=True),
            self.assertRaises(RuntimeError),
        ):
            require_connected_database(connection)


if __name__ == "__main__":
    unittest.main()
