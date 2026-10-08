from django.apps import AppConfig


class PaymentProviderConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.payment_provider"
    label = "payment_provider"
