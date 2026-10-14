import hashlib
import json
import os
import subprocess
import sys
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


@pytest.mark.django_db
@override_settings(ALLOWED_HOSTS=["testserver"], RODADA_BFF_HOST_SECRET=SECRET)
def test_non_ascii_signature_is_rejected_without_server_error(client):
    assertion = signed("e2ea.rodada.bar", method="/ready/")
    assertion["HTTP_X_RODADA_BFF_SIGNATURE"] = "é" * 64
    response = client.get("/ready/", **assertion)
    assert response.status_code == 403
    assert response.json()["code"] == "HOST_ASSERTION_INVALID"


@pytest.mark.django_db
@override_settings(ALLOWED_HOSTS=["testserver"], RODADA_BFF_HOST_SECRET=SECRET)
@pytest.mark.parametrize("host", [
    "e2ea.rodada.bar:evil", "e2ea.rodada.bar:99999", "e2ea.rodada.bar:0",
    "e2ea.rodada.bar@evil.invalid", "e2ea.rodada.bar.evil.invalid",
    "ｅ2ea.rodada.bar", "e2ea.rodada.bar ",
])
def test_signed_malformed_or_lookalike_authority_fails_closed(client, host):
    venue = Venue.objects.create(name="A", slug="authority-a")
    VenueDomain.objects.create(venue=venue, hostname="e2ea.rodada.bar",
                               is_active=True, is_verified=True)
    response = client.get("/venue/context/", **signed(host, method="/venue/context/"))
    assert response.status_code in (403, 421)
    assert "venue" not in response.json()


@pytest.mark.django_db
@override_settings(ALLOWED_HOSTS=["testserver", "api.rodada.bar", "localhost"],
                   RODADA_BFF_HOST_SECRET=SECRET)
def test_signed_valid_ports_and_explicit_compatibility_hosts(client):
    venue = Venue.objects.create(name="A", slug="valid-authority-a")
    VenueDomain.objects.create(venue=venue, hostname="e2ea.rodada.bar",
                               is_active=True, is_verified=True)
    for host in ("e2ea.rodada.bar:443", "E2EA.RODADA.BAR:3130"):
        response = client.get("/venue/context/", **signed(host, method="/venue/context/"))
        assert response.status_code == 200
        assert response.json()["venue"]["id"] == str(venue.pk)
    for host in ("localhost:3130", "api.rodada.bar"):
        assert client.get("/ready/", **signed(host, method="/ready/")).status_code == 200


@pytest.mark.django_db
@override_settings(ALLOWED_HOSTS=["testserver"], RODADA_BFF_HOST_SECRET=SECRET)
def test_assertion_cannot_be_reused_for_other_method_or_path(client):
    assertion = signed("testserver", method="/ready/")
    assert client.get("/health/", **assertion).status_code == 403
    assert client.post("/ready/", **assertion).status_code == 403


@pytest.mark.parametrize("additional,expected", [
    ("", ["localhost", "api.rodada.bar"]),
    (" e2ea.rodada.bar, e2eb.rodada.bar, ",
     ["localhost", "api.rodada.bar", "e2ea.rodada.bar", "e2eb.rodada.bar"]),
])
def test_additional_ingress_hosts_preserve_existing_django_allowlist(additional, expected):
    # Fresh interpreter proves env-based settings without mutating Django test settings.
    env = {**os.environ, "DJANGO_ALLOWED_HOSTS": "localhost,api.rodada.bar",
           "DJANGO_ADDITIONAL_ALLOWED_HOSTS": additional, "RODADA_RELEASE_MODE": "pilot"}
    result = subprocess.run(
        [sys.executable, "-c", "import json; from rodada_api.settings import ALLOWED_HOSTS; print(json.dumps(ALLOWED_HOSTS))"],
        env=env, capture_output=True, text=True, check=True,
    )
    hosts = json.loads(result.stdout)
    assert hosts == expected
    assert "unregistered-preview.rodada.bar" not in hosts

