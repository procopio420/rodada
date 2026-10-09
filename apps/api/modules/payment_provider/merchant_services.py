"""OAuth connection/refresh/disconnect; credentials never leave the backend."""

import hashlib
import json
import secrets
from datetime import timedelta
from urllib.parse import urlencode
from urllib.request import Request, build_opener

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from modules.audit.services import record_audit_event

from .credentials import seal, unseal
from .models import DeviceAuthorization, MerchantConnection, OAuthAuthorization
from .paytime import NoRedirect
from .services import ProviderServiceError, _PENDING_STATUSES
from modules.ledger.models import Payment


def _oauth_config():
    config = getattr(settings, "RODADA_SUMUP_OAUTH", {})
    if not all(config.get(k) for k in ("client_id", "client_secret", "redirect_uri")):
        raise ProviderServiceError("OAUTH_NOT_CONFIGURED", "Conexão SumUp indisponível.", 409)
    return config


def oauth_transport(path, body=None, access_token=None):
    req = Request(
        "https://api.sumup.com" + path,
        method="POST" if body is not None else "GET",
        data=urlencode(body).encode() if body is not None else None,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            **({"Authorization": f"Bearer {access_token}"} if access_token else {}),
        },
    )
    with build_opener(NoRedirect()).open(req, timeout=15) as response:
        return json.loads(response.read(200_000))


@transaction.atomic
def begin_connection(actor):
    config = _oauth_config()
    state = secrets.token_urlsafe(32)
    OAuthAuthorization.objects.create(
        venue_id=actor.venue_id,
        staff_id=actor.staff_id,
        state_hash=hashlib.sha256(state.encode()).hexdigest(),
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    record_audit_event(actor=actor, event_type="payment.merchant_connection_started")
    return "https://api.sumup.com/authorize?" + urlencode(
        {
            "response_type": "code",
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
            "scope": "payments transactions.history user.profile_readonly",
            "state": state,
        }
    )


def consume_authorization(*, actor, state):
    with transaction.atomic():
        authorization = (
            OAuthAuthorization.objects.select_for_update()
            .filter(
                state_hash=hashlib.sha256(state.encode()).hexdigest(),
                venue_id=actor.venue_id,
                staff_id=actor.staff_id,
                consumed_at__isnull=True,
                expires_at__gt=timezone.now(),
            )
            .first()
        )
        if authorization is None:
            raise ProviderServiceError(
                "INVALID_OAUTH_STATE", "Autorização inválida ou expirada.", 409
            )
        authorization.consumed_at = timezone.now()
        authorization.save(update_fields=["consumed_at"])


def complete_connection(*, actor, state, code, transport=oauth_transport):
    config = _oauth_config()
    consume_authorization(actor=actor, state=state)
    # Single use even when exchange result is unknown; never blindly exchange again.
    tokens = transport(
        "/token",
        {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "redirect_uri": config["redirect_uri"],
        },
    )
    profile = transport("/v0.1/me", access_token=tokens["access_token"])
    merchant_code = profile["merchant_profile"]["merchant_code"]
    scopes = tokens.get("scope", "").split()
    if "payments" not in scopes or not {"transactions.history", "transactions.read"}.intersection(
        scopes
    ):
        raise ProviderServiceError(
            "SUMUP_SCOPE_REQUIRED",
            "SumUp precisa autorizar payments e consulta de transações.",
            409,
        )
    with transaction.atomic():
        connection, _ = MerchantConnection.objects.get_or_create(
            venue_id=actor.venue_id, provider="sumup", merchant_code=merchant_code
        )
        connection = MerchantConnection.objects.select_for_update().get(pk=connection.pk)
        connection.encrypted_credentials = seal(
            connection,
            {"access_token": tokens["access_token"], "refresh_token": tokens["refresh_token"]},
        )
        connection.token_expires_at = timezone.now() + timedelta(seconds=int(tokens["expires_in"]))
        connection.scopes = scopes
        connection.active = True
        connection.disconnected_at = None
        # Merchant eligibility still requires explicit configuration/approval.
        connection.save()
        record_audit_event(
            actor=actor,
            event_type="payment.merchant_connected",
            entity_type="MerchantConnection",
            entity_id=str(connection.pk),
            metadata={"merchant_code": merchant_code},
        )
    return connection


@transaction.atomic
def access_token_for(connection_id, *, venue_id, transport=oauth_transport, historical=False):
    connection = MerchantConnection.objects.select_for_update().get(
        pk=connection_id, venue_id=venue_id, **({"active": True} if not historical else {})
    )
    credentials = unseal(connection)
    if connection.token_expires_at and connection.token_expires_at > timezone.now() + timedelta(
        seconds=60
    ):
        return credentials["access_token"]
    config = _oauth_config()
    try:
        result = transport(
            "/token",
            {
                "grant_type": "refresh_token",
                "refresh_token": credentials["refresh_token"],
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
            },
        )
    except Exception as error:
        # Transport outages preserve credentials; no automatic repeated exchange in this request.
        raise ProviderServiceError(
            "MERCHANT_REAUTH_REQUIRED", "Revalide a conexão SumUp.", 409
        ) from error
    if result.get("error"):
        raise ProviderServiceError("MERCHANT_REAUTH_REQUIRED", "Reautorize a conexão SumUp.", 409)
    credentials["access_token"] = result["access_token"]
    credentials["refresh_token"] = result.get("refresh_token", credentials["refresh_token"])
    connection.encrypted_credentials = seal(connection, credentials)
    connection.token_expires_at = timezone.now() + timedelta(seconds=int(result["expires_in"]))
    connection.save(update_fields=["encrypted_credentials", "token_expires_at"])
    return credentials["access_token"]


@transaction.atomic
def disconnect_connection(*, connection_id, actor):
    connection = MerchantConnection.objects.select_for_update().get(
        pk=connection_id, venue_id=actor.venue_id
    )
    payments = Payment.objects.filter(
        tab__venue_id=connection.venue_id,
        provider=f"{connection.provider}:{connection.venue_id}:{connection.merchant_code}",
    )
    if payments.filter(status__in=_PENDING_STATUSES).exists():
        raise ProviderServiceError(
            "MERCHANT_PAYMENTS_PENDING",
            "Reconcilie os pagamentos pendentes antes de desconectar o estabelecimento.",
            409,
        )
    if not connection.active:
        return connection
    connection.active = False
    # Confirmed payments may still need authenticated lookup/refund. Never erase
    # their historical credentials as a side effect of disabling new collections.
    if not payments.exists():
        connection.encrypted_credentials = ""
    connection.disconnected_at = timezone.now()
    connection.save(update_fields=["active", "encrypted_credentials", "disconnected_at"])
    DeviceAuthorization.objects.filter(connection=connection).update(active=False)
    record_audit_event(
        actor=actor,
        event_type="payment.merchant_disconnected",
        entity_type="MerchantConnection",
        entity_id=str(connection.pk),
    )
    # Local revocation only. No undocumented SumUp token-revocation endpoint.
