from django.apps import AppConfig


class RealtimeConfig(AppConfig):
    name = "modules.realtime"

    def ready(self):
        from . import signals  # noqa: F401
