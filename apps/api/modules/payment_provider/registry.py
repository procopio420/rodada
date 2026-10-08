"""Explicit tenant/method selection; historical attempts keep their provider."""

from django.conf import settings

from .fake import DeterministicFakePaymentProvider
from .merchant_services import access_token_for
from .models import MerchantConnection
from .paytime import PaytimePixProvider
from .services import ProviderServiceError
from .sumup import SumUpPixProvider, SumUpTapToPayProvider


def provider_for_venue(venue_id, method="PIX", provider_key=None):
    config = dict(getattr(settings, "RODADA_PAYMENT_PROVIDERS", {}).get(str(venue_id), {}))
    if not config:
        raise ProviderServiceError(
            "PROVIDER_NOT_CONFIGURED", "Pagamento integrado indisponível.", 409
        )
    kind = config.pop("provider", "paytime")
    if provider_key and provider_key.startswith("paytime:"):
        kind = "paytime"
        config = dict(getattr(settings, "RODADA_PAYTIME_PROVIDERS", {}).get(str(venue_id), config))
        config.pop("provider", None)
    try:
        if kind == "simulator":
            if not settings.DEBUG or not getattr(settings, "RODADA_PAYMENT_SIMULATION", False):
                raise ValueError("Simulation is disabled")
            provider = DeterministicFakePaymentProvider(venue_id=venue_id, **config)
        elif kind == "sumup":
            connection = MerchantConnection.objects.get(
                pk=config.pop("connection_id"),
                venue_id=venue_id,
                provider="sumup",
                active=True,
                simulated=False,
            )
            if not connection.capabilities.get("pix" if method == "PIX" else "tap_to_pay"):
                raise ValueError("Merchant capability not authorized")
            token = access_token_for(connection.pk, venue_id=venue_id)
            adapter = SumUpPixProvider if method == "PIX" else SumUpTapToPayProvider
            provider = adapter(
                venue_id=venue_id,
                merchant_code=connection.merchant_code,
                access_token=token,
                **config,
            )
        elif kind == "paytime":
            provider = PaytimePixProvider(venue_id=venue_id, **config)
        else:
            raise ValueError("Unknown provider")
        if provider_key and provider.provider_key != provider_key:
            raise ValueError("Historical provider configuration required")
        return provider
    except (TypeError, ValueError, MerchantConnection.DoesNotExist) as error:
        raise ProviderServiceError(
            "PROVIDER_NOT_CONFIGURED", "Pagamento integrado indisponível.", 409
        ) from error
