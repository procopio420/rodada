"""Disposable printing/concurrency database. Never uses production DATABASE_URL."""

import os
from .settings_test import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "rodada_printing_test",
        "USER": os.environ.get("PRINTING_TEST_DB_USER", "rodada"),
        "PASSWORD": os.environ.get("PRINTING_TEST_DB_PASSWORD", "rodada-test"),
        "HOST": "127.0.0.1",
        "PORT": os.environ.get("PRINTING_TEST_DB_PORT", "55451"),
    }
}
