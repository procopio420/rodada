"""Tenant-bound AEAD storage; deployment owns key provisioning and rotation."""

import base64
import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings


def _cipher():
    key = base64.b64decode(settings.RODADA_PAYMENT_CREDENTIAL_KEY, validate=True)
    if len(key) != 32:
        raise ValueError("Payment credential encryption requires a 32-byte key")
    return AESGCM(key)


def _aad(connection):
    return f"{connection.venue_id}:{connection.provider}:{connection.merchant_code}:{connection.pk}".encode()


def seal(connection, credentials):
    nonce = os.urandom(12)
    encrypted = _cipher().encrypt(nonce, json.dumps(credentials).encode(), _aad(connection))
    return base64.b64encode(nonce + encrypted).decode()


def unseal(connection):
    value = base64.b64decode(connection.encrypted_credentials, validate=True)
    return json.loads(_cipher().decrypt(value[:12], value[12:], _aad(connection)))
