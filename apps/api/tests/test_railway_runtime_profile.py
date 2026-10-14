"""Preflight must reject unsafe pilot configuration before database contact."""
import os
import subprocess
from pathlib import Path

import pytest

PROFILE = Path(__file__).resolve().parents[3] / "deploy/railway/runtime-profile.sh"
SECRET = "test-only-" + "aBcdEfGhIjKlMnOpQrStUvWxYz0123456789" * 2


def run_profile(**overrides):
    env = {**os.environ, "RODADA_RELEASE_MODE": "pilot", "DJANGO_SECRET_KEY": SECRET,
           "RODADA_BFF_HOST_SECRET": SECRET,
           "RODADA_ENABLE_TENANT_HOST_UI": "false", "RODADA_DEMO_SEED_ON_START": "true",
           "DJANGO_DEBUG": "false", "RODADA_PAYMENT_SIMULATION": "false", **overrides}
    return subprocess.run(["bash", "-c", 'source "$1"; printf "%s %s %s" "$RODADA_RELEASE_MODE" "$DJANGO_DEBUG" "$RODADA_PAYMENT_SIMULATION"', "test", str(PROFILE)], env=env, capture_output=True, text=True, check=False)


@pytest.mark.parametrize("overrides", [
    {"RODADA_RELEASE_MODE": "production"}, {"DJANGO_DEBUG": "true"},
    {"RODADA_PAYMENT_SIMULATION": "true"}, {"DJANGO_SECRET_KEY": "dev-only-change-me"},
    {"DJANGO_SECRET_KEY": "x" * 80}, {"DJANGO_SECRET_KEY": "ci-local-" + SECRET},
])
def test_unsafe_profile_fails_without_exposing_secret(overrides):
    result = run_profile(**overrides)
    assert result.returncode != 0
    assert result.stdout == ""
    assert overrides.get("DJANGO_SECRET_KEY", SECRET) not in result.stderr


def test_secure_pilot_and_default_demo_profiles():
    result = run_profile()
    assert result.returncode == 0 and result.stdout == "pilot false false"
    result = run_profile(RODADA_RELEASE_MODE="demo", DJANGO_SECRET_KEY="disposable", DJANGO_DEBUG="true")
    assert result.returncode == 0 and result.stdout == "demo false false"


@pytest.mark.parametrize("secret", ["", "short", "a" * 64])
def test_pilot_rejects_missing_or_weak_bff_secret_before_database_contact(secret):
    result = run_profile(RODADA_BFF_HOST_SECRET=secret)
    assert result.returncode != 0
    assert "RODADA_BFF_HOST_SECRET" in result.stderr
    assert result.stdout == ""
    if secret:
        assert secret not in result.stderr


def test_shared_demo_tenant_activation_refuses_automatic_seed():
    result = run_profile(RODADA_RELEASE_MODE="demo", RODADA_ENABLE_TENANT_HOST_UI="true")
    assert result.returncode != 0
    assert result.stdout == ""
    assert "RODADA_DEMO_SEED_ON_START=false" in result.stderr


@pytest.mark.parametrize("secret", ["", "short", "a" * 64])
def test_shared_demo_tenant_activation_requires_explicit_strong_hmac(secret):
    result = run_profile(RODADA_RELEASE_MODE="demo", RODADA_ENABLE_TENANT_HOST_UI="true",
                         RODADA_DEMO_SEED_ON_START="false", RODADA_BFF_HOST_SECRET=secret)
    assert result.returncode != 0
    assert result.stdout == ""
    assert "RODADA_BFF_HOST_SECRET" in result.stderr


def test_shared_demo_tenant_activation_accepts_seed_disabled_and_valid_hmac():
    result = run_profile(RODADA_RELEASE_MODE="demo", RODADA_ENABLE_TENANT_HOST_UI="true",
                         RODADA_DEMO_SEED_ON_START="false")
    assert result.returncode == 0
    assert result.stdout == "demo false false"


@pytest.mark.parametrize("value", ["", "TRUE", "0", "unexpected"])
def test_invalid_seed_switch_fails_closed(value):
    result = run_profile(RODADA_RELEASE_MODE="demo", RODADA_DEMO_SEED_ON_START=value)
    assert result.returncode != 0
    assert result.stdout == ""
