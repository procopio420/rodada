from pathlib import Path
import os

from corsheaders.defaults import default_headers

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "rodada-local-only-secret")
DEBUG = os.environ.get("DEBUG", "1") == "1"
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions",
    "django.contrib.messages", "django.contrib.staticfiles", "rest_framework", "corsheaders", "channels",
    "catalog", "pos", "ledger", "cash", "audit", "fulfillment", "customers", "dispatch",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "corsheaders.middleware.CorsMiddleware", "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True, "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DATABASES = {"default": {
    "ENGINE": os.environ.get("DJANGO_DB_ENGINE", "django.db.backends.sqlite3"),
    "NAME": os.environ.get("DJANGO_DB_NAME", BASE_DIR / "db.sqlite3"),
    "USER": os.environ.get("DJANGO_DB_USER", ""), "PASSWORD": os.environ.get("DJANGO_DB_PASSWORD", ""),
    "HOST": os.environ.get("DJANGO_DB_HOST", ""), "PORT": os.environ.get("DJANGO_DB_PORT", ""),
}}
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if origin.strip()]
# The staff web client identifies the active operator on every API request.
# Custom request headers must be explicitly allowed by the CORS preflight.
CORS_ALLOW_HEADERS = (*default_headers, "x-staff-id")
REST_FRAMEWORK = {"DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"], "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"]}

if os.environ.get("REDIS_URL"):
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [os.environ["REDIS_URL"]]},
        }
    }
else:
    # Local development remains self-contained; production should set REDIS_URL.
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
