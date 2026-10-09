"""PostgreSQL test settings; use a dedicated disposable database."""
import os

from .settings_test import *  # noqa: F403

DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ.get("POSTGRES_DB", "rodada_pricing"),
    "USER": os.environ.get("POSTGRES_USER", "rodada"),
    "PASSWORD": os.environ["POSTGRES_PASSWORD"],
    "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
    "PORT": os.environ.get("POSTGRES_PORT", "5432"),
}}
