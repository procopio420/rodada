"""Verify the original tenant Host through a signed, short-lived BFF assertion."""
import hashlib
import hmac
import time
from django.conf import settings
from django.http import JsonResponse
from .domain_resolution import resolve_venue_domain
from .hostnames import TENANT_DOMAIN, resolved_venue_id

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
            if not secret or not fresh or not claimed or not signature or not hmac.compare_digest(expected, signature):
                return JsonResponse({"code": "HOST_ASSERTION_INVALID"}, status=403)
            host = claimed.lower()
        hostname = host.split(":")[0]
        if hostname.endswith("." + TENANT_DOMAIN):
            domain = resolve_venue_domain(hostname)
            if domain is None:
                return JsonResponse({"code": "VENUE_HOST_NOT_FOUND"}, status=421)
            venue_id = domain.venue_id
            # Only the Next BFF may use canonical tenant API paths;
            # native clients and payment callbacks use the shared API host.
            if not signed and request.path not in ("/health/", "/ready/", "/venue/context/"):
                return JsonResponse({"code": "HOST_ASSERTION_REQUIRED"}, status=403)
        else:
            venue_id = None
        token = resolved_venue_id.set(venue_id)
        try:
            return self.get_response(request)
        finally:
            resolved_venue_id.reset(token)
