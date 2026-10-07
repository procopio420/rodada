import os

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = [
    host
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host
]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
    "modules.venue",
    "modules.access",
    "modules.catalog",
    "modules.ordering",
    "modules.hospitality",
    "modules.dispatch",
    "modules.ledger",
    "modules.audit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "rodada_api.urls"
TEMPLATES = []
WSGI_APPLICATION = "rodada_api.wsgi.application"
ASGI_APPLICATION = "rodada_api.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DJANGO_DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.environ.get("POSTGRES_DB", "rodada"),
        "USER": os.environ.get("POSTGRES_USER", "rodada"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "rodada"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

RODADA_ACCESS_TOKEN_TTL_SECONDS = int(os.environ.get("RODADA_ACCESS_TOKEN_TTL_SECONDS", "900"))
RODADA_REFRESH_TOKEN_TTL_SECONDS = int(os.environ.get("RODADA_REFRESH_TOKEN_TTL_SECONDS", "43200"))
RODADA_PIN_FAILURE_THRESHOLD = int(os.environ.get("RODADA_PIN_FAILURE_THRESHOLD", "5"))
RODADA_PIN_BACKOFF_BASE_SECONDS = int(os.environ.get("RODADA_PIN_BACKOFF_BASE_SECONDS", "15"))
RODADA_PIN_BACKOFF_MAX_SECONDS = int(os.environ.get("RODADA_PIN_BACKOFF_MAX_SECONDS", "300"))
RODADA_REAUTH_WINDOW_SECONDS = int(os.environ.get("RODADA_REAUTH_WINDOW_SECONDS", "300"))

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "modules.access.authentication.StaffBearerAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "credential_redaction": {
            "()": "modules.access.logging.CredentialRedactionFilter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["credential_redaction"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
    },
}
