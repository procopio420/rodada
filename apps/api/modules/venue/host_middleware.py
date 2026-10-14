"""Verify the original tenant Host through a signed, short-lived BFF assertion."""
import hashlib
import hmac
import time
from django.conf import settings
from django.http import JsonResponse
from django.http.request import split_domain_port, validate_host
from .domain_resolution import resolve_venue_domain
from .hostnames import TENANT_DOMAIN, RESERVED_LABELS, resolved_venue_id

class VenueHostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().lower()
        claimed = request.headers.get("X-Rodada-Bff-Host")
        timestamp = request.headers.get("X-Rodada-Bff-Time")
        signature = request.headers.get("X-Rodada-Bff-Signature")
        signed = claimed is not None or timestamp is not None or signature is not None
        if signed:
            secret = settings.RODADA_BFF_HOST_SECRET
            try:
                fresh = abs(time.time() - int(timestamp or "")) <= 60
            except ValueError:
                fresh = False
            message = f"{timestamp}\n{request.method}\n{request.path}\n{claimed}"
            expected = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
            if not secret or not fresh or not claimed or not signature or not signature.isascii() or not hmac.compare_digest(expected, signature):
                return JsonResponse({"code": "HOST_ASSERTION_INVALID"}, status=403)
            host = claimed.lower()
        hostname, port = split_domain_port(host)
        if not hostname or (port and (len(port) > 5 or not 1 <= int(port) <= 65535)):
            return JsonResponse({"code": "HOST_ASSERTION_INVALID"}, status=403)
        label = hostname[: -len("." + TENANT_DOMAIN)] if hostname.endswith("." + TENANT_DOMAIN) else ""
        if label and label not in RESERVED_LABELS:
            domain = resolve_venue_domain(hostname)
            if domain is None:
                return JsonResponse({"code": "VENUE_HOST_NOT_FOUND"}, status=421)
            venue_id = domain.venue_id
            # Only the Next BFF may use canonical tenant API paths;
            # native clients and payment callbacks use the shared API host.
            if not signed and request.path not in ("/health/", "/ready/", "/venue/context/"):
                return JsonResponse({"code": "HOST_ASSERTION_REQUIRED"}, status=403)
        else:
            # Compatibility hosts are explicit ingress configuration, not an
            # escape hatch for a signed lookalike outside the tenant domain.
            if signed and not validate_host(hostname, settings.ALLOWED_HOSTS):
                return JsonResponse({"code": "HOST_ASSERTION_INVALID"}, status=403)
            venue_id = None
        # Preserve only the already-validated tenant Host for lazy SSE reauthorization.
        # Raw browser forwarding headers must never become stream authority.
        request.venue_hostname = hostname if venue_id is not None else None
        token = resolved_venue_id.set(venue_id)
        try:
            return self.get_response(request)
        finally:
            resolved_venue_id.reset(token)
