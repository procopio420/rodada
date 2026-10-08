"""Merchant secrets are server-side settings, never returned to clients."""
from django.conf import settings
from .paytime import PaytimePixProvider
from .services import ProviderServiceError


def provider_for_venue(venue_id):
    config = getattr(settings, "RODADA_PAYMENT_PROVIDERS", {}).get(str(venue_id))
    if not config:
        raise ProviderServiceError("PROVIDER_NOT_CONFIGURED", "Pagamento integrado indisponível.", 409)
    try:
        return PaytimePixProvider(venue_id=venue_id, **config)
    except (TypeError, ValueError) as error:
        raise ProviderServiceError("PROVIDER_NOT_CONFIGURED", "Pagamento integrado indisponível.", 409) from error
