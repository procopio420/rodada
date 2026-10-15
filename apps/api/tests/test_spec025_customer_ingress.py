"""The native identity API must not fall through to opaque Next guest pages."""

import re
from pathlib import Path

import pytest

TEMPLATE = Path(__file__).resolve().parents[3] / "deploy/railway/nginx.conf.tpl"


@pytest.mark.parametrize("action", ["register", "login", "context", "claim", "logout", "password"])
@pytest.mark.parametrize("suffix", ["", "/"])
def test_customer_api_uses_raw_django_with_untrusted_assertions_stripped(action, suffix):
    location = re.search(r"location ~ (\S+) \{(.*?)\n    }", TEMPLATE.read_text(), re.DOTALL)
    assert location
    assert re.match(location[1], f"/guest/customer/{action}{suffix}")
    assert "proxy_pass http://127.0.0.1:8000;" in location[2]
    for header in ("Host", "Time", "Signature"):
        assert f'proxy_set_header X-Rodada-Bff-{header} "";' in location[2]
    assert "proxy_set_header Host $http_host;" in location[2]


@pytest.mark.parametrize(
    "path",
    [
        "/guest/customer",
        "/guest/customer/",
        "/guest/customer-token",
        "/guest/customer/login-extra/",
        "/guest/customer/login/extra/",
        "/api/guest/customer/login",
        "/guest/qr-test-token",
        "/manage",
        "/cash",
    ],
)
def test_identity_route_does_not_capture_guest_pages_bff_or_lookalikes(path):
    location = re.search(r"location ~ (\S+) \{", TEMPLATE.read_text())
    assert location and not re.match(location[1], path)
