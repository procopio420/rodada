import pytest
from django.core.exceptions import ValidationError
from modules.venue.hostnames import normalize_tenant_hostname

@pytest.mark.parametrize("host", [
    "rodada.bar", "app.rodada.bar", "api.rodada.bar",
    "foo.bar.rodada.bar", "foo.rodada.bar.evil",
    "foo.rodada.bar:443", "-foo.rodada.bar",
    "foo-.rodada.bar", "foo_bar.rodada.bar",
    "foo.rodada.ai", "",
])
def test_rejects_invalid_host(host):
    with pytest.raises(ValidationError):
        normalize_tenant_hostname(host)


def test_pilot_host():
    assert normalize_tenant_hostname("BarDoAderlan.Rodada.Bar") == "bardoaderlan.rodada.bar"
