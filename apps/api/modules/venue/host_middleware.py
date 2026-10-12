"""Host restriction for all HTTP entry points, including anonymous guest flows.

The BFF authenticates the original Host with a short-lived HMAC assertion.
Direct API/native requests use their actual Host and explicit transport allowlist.
"""

import hashlib
import hmac
import time

from django.conf import settings
from django.http import JsonResponse

from .hostnames import HostResolutionError, resolve_venue_from_hostname, resolved_venue_id


def request_hostname(request):
    # get_host validates ALLOWED_HOSTS; USE_X_FORWARDED_HOST must remain False.
    actual = request.get_host().lower()
    claimed = request.headers.get("X-Rodada-Bff-Host")
    if claimed is not None:
        secret = settings.RODADA_BFF_HOST_SECRET
        timestamp = request.headers.get("X-Rodada-Bff-Time", "")
        signature = request.headers.get("X-Rodada-Bff-Signature", "")
        try:
            fresh = abs(time.time() - int(timestamp)) <= 60
        except ValueError:
            fresh = False
        message = f"{timestamp}\n{request.method}\n{request.path}\n{claimed}"
        expected = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
        if not secret or not fresh or not hmac.compare_digest(expected, signature):
            raise HostResolutionError("HOST_ASSERTION_INVALID", 403)
        actual = claimed.lower()
    elif any(
        request.headers.get(name) is not None
        for name in ("X-Rodada-Bff-Time", "X-Rodada-Bff-Signature")
    ):
        raise HostResolutionError("HOST_ASSERTION_INVALID", 403)
    # Ports belong to HTTP authority, not registry keys; validate them before lookup.
    if actual in settings.RODADA_HOST_COMPATIBILITY_HOSTS:
        return None
    host, separator, port = actual.partition(":")
    if separator and (not port.isdigit() or not 1 <= int(port) <= 65535):
        raise HostResolutionError()
    if host in settings.RODADA_HOST_COMPATIBILITY_HOSTS:
        return None
    return host


class VenueHostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            hostname = request_hostname(request)
            venue = resolve_venue_from_hostname(hostname) if hostname is not None else None
        except HostResolutionError as exc:
            return JsonResponse(
                {"code": exc.code, "message": "Host de estabelecimento inválido."},
                status=exc.status_code,
            )
        request.host_venue = venue
        request.venue_hostname = hostname
        token = resolved_venue_id.set(venue.pk if venue else None)
        try:
            return self.get_response(request)
        finally:
            resolved_venue_id.reset(token)
