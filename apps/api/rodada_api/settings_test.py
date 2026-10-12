from .settings import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

RODADA_HOST_COMPATIBILITY_HOSTS = ("testserver", "localhost", "127.0.0.1")
