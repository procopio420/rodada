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
    from modules.venue.hostnames import assert_staff_venue, assert_guest_venue
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
