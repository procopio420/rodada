import hashlib
import hmac
import time
import pytest
from django.test import override_settings
from modules.venue.models import Venue, VenueDomain
from modules.venue.hostnames import resolved_venue_id, assert_staff_venue, assert_guest_venue
from modules.access.services import AccessServiceError
from modules.guest_access.services import GuestAccessError

SECRET = "test-secret-only"


def signed(host, method="/", timestamp=None, verb="GET"):
    timestamp = str(int(time.time()) if timestamp is None else timestamp)
    message = f"{timestamp}\n{verb}\n{method}\n{host}"
    signature = hmac.new(SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()
    return {"HTTP_X_RODADA_BFF_HOST": host, "HTTP_X_RODADA_BFF_TIME": timestamp,
            "HTTP_X_RODADA_BFF_SIGNATURE": signature}


@pytest.mark.django_db
@override_settings(ALLOWED_HOSTS=["testserver", "localhost"], RODADA_BFF_HOST_SECRET=SECRET)
def test_host_assertion_rejects_tampering_and_expiration(client):
    valid = signed("bardoaderlan.rodada.bar")
    assert client.get("/", **{**valid, "HTTP_X_RODADA_BFF_SIGNATURE": "0" * 64}).status_code == 403
    assert client.get("/", **signed("bardoaderlan.rodada.bar", timestamp=int(time.time()) - 120)).status_code == 403
    assert client.get("/", HTTP_X_RODADA_BFF_HOST="bardoaderlan.rodada.bar").status_code == 403
    assert client.get("/", **signed("outrobar.rodada.bar")).status_code == 421


@pytest.mark.django_db
@override_settings(ALLOWED_HOSTS=["testserver"], RODADA_BFF_HOST_SECRET=SECRET)
def test_verified_host_is_bound_to_staff_and_guest_context(client):
    first = Venue.objects.create(name="Aderlan", slug="bar-do-aderlan")
    second = Venue.objects.create(name="Other", slug="other")
    VenueDomain.objects.create(venue=first, hostname="bardoaderlan.rodada.bar", is_active=True, is_verified=True)
    VenueDomain.objects.create(venue=second, hostname="outrobar.rodada.bar", is_active=True, is_verified=True)
    token = resolved_venue_id.set(first.pk)
    try:
        assert_staff_venue(first.pk)
        assert_guest_venue(first.pk)
        with pytest.raises(AccessServiceError) as exc:
            assert_staff_venue(second.pk)
        assert exc.value.code == "VENUE_HOST_MISMATCH"
        with pytest.raises(GuestAccessError) as exc:
            assert_guest_venue(second.pk)
        assert exc.value.code == "QR_NOT_FOUND"
    finally:
        resolved_venue_id.reset(token)
    # A signed request to a real hostname is allowed past host resolution.
    assert client.get("/", **signed("bardoaderlan.rodada.bar")).status_code != 421


@pytest.mark.django_db
@override_settings(ALLOWED_HOSTS=["testserver", "bardoaderlan.rodada.bar"], RODADA_BFF_HOST_SECRET=SECRET)
def test_tenant_direct_api_cannot_bypass_signed_bff(client):
    venue = Venue.objects.create(name="Aderlan", slug="bar-do-aderlan")
    VenueDomain.objects.create(venue=venue, hostname="bardoaderlan.rodada.bar",
                               is_active=True, is_verified=True)
    origin = {"HTTP_HOST": "bardoaderlan.rodada.bar"}
    for path in ("/auth/login/", "/guest/qr/resolve/", "/tabs/", "/cash/shifts/"):
        response = client.post(path, data={}, content_type="application/json", **origin)
        assert response.status_code == 403
        assert response.json()["code"] == "HOST_ASSERTION_REQUIRED"
    assert client.get("/health/", **origin).status_code == 200
    response = client.get("/venue/context/", **origin)
    assert response.status_code == 200
    assert response.json()["venue"]["id"] == str(venue.pk)
    bff = signed("bardoaderlan.rodada.bar", method="/auth/login/", verb="POST")
    assert client.post("/auth/login/", data={}, content_type="application/json", **bff).status_code == 400
    assert client.get("/health/", HTTP_X_FORWARDED_HOST="bardoaderlan.rodada.bar").status_code == 200


@pytest.mark.django_db
@override_settings(ALLOWED_HOSTS=["api.rodada.bar", "testserver"], RODADA_BFF_HOST_SECRET=SECRET)
def test_reserved_shared_api_host_remains_legacy_for_native_clients_and_webhooks(client):
    # api.rodada.bar is a reserved infrastructure hostname, NEVER a Venue.
    response = client.get("/ready/", HTTP_HOST="api.rodada.bar")
    assert response.status_code == 200
    response = client.post("/auth/login/", data={}, content_type="application/json",
                           HTTP_HOST="api.rodada.bar")
    assert response.status_code == 400
    # A forged assertion on the shared API hostname still fails authentication.
    response = client.get("/ready/", HTTP_HOST="api.rodada.bar",
                          HTTP_X_RODADA_BFF_HOST="outrobar.rodada.bar")
    assert response.status_code == 403
