"""Dedicated disposable PostgreSQL customization/concurrency verification."""

from .settings_test import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "rodada_customization_test",
        "USER": "rodada",
        "PASSWORD": "rodada-test",
        "HOST": "127.0.0.1",
        "PORT": "55449",
    }
}
