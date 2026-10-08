"""Disposable PostgreSQL validation; never points at the production database."""
import os
from .settings_test import *  # noqa: F403

DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql",
    "NAME": "rodada_payments_test", "USER": os.environ.get("PAYMENTS_TEST_DB_USER", "rodada"),
    "PASSWORD": os.environ.get("PAYMENTS_TEST_DB_PASSWORD", "rodada-test"),
    "HOST": "127.0.0.1", "PORT": os.environ.get("PAYMENTS_TEST_DB_PORT", "55447")}}
