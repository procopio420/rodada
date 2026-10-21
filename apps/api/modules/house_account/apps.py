from django.apps import AppConfig


class HouseAccountConfig(AppConfig):
    name = "modules.house_account"

    def ready(self):
        from . import signals  # noqa: F401
