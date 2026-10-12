"""Disposable Spec 025 database, explicitly separate from any operational database."""

import os
from .settings_test import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "rodada_spec025",
        "USER": os.environ.get("SPEC025_DB_USER", "lucas"),
        "PASSWORD": os.environ.get("SPEC025_DB_PASSWORD", ""),
        "HOST": "127.0.0.1",
        "PORT": os.environ.get("SPEC025_DB_PORT", "55475"),
    }
}
