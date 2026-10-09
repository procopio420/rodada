import os
from pathlib import Path
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def check_profile(**overrides):
    env = {k: v for k, v in os.environ.items() if k not in (
        "DJANGO_SECRET_KEY", "DJANGO_ALLOWED_HOSTS", "DJANGO_CSRF_TRUSTED_ORIGINS")}
    env.update(overrides)
    return subprocess.run([sys.executable, "manage.py", "check", "--deploy",
        "--fail-level", "ERROR", "--settings=rodada_api.settings_production"],
        cwd=ROOT, env=env, capture_output=True, text=True)


def test_production_refuses_missing_secret():
    result = check_profile(DJANGO_ALLOWED_HOSTS="api.rodada.ai")
    assert result.returncode != 0
    assert "Provision a high-entropy" in result.stderr


def test_production_refuses_wildcard_host_and_insecure_origin():
    secret = secrets.token_urlsafe(64)
    result = check_profile(DJANGO_SECRET_KEY=secret, DJANGO_ALLOWED_HOSTS="*")
    assert result.returncode != 0
    assert "explicit DJANGO_ALLOWED_HOSTS" in result.stderr
    result = check_profile(DJANGO_SECRET_KEY=secret, DJANGO_ALLOWED_HOSTS="api.rodada.ai",
        DJANGO_CSRF_TRUSTED_ORIGINS="http://gerencia.rodada.ai")
    assert result.returncode != 0
    assert "explicit HTTPS origins" in result.stderr


def test_production_deploy_check_preserves_preload_warning():
    result = check_profile(DJANGO_SECRET_KEY=secrets.token_urlsafe(64),
        DJANGO_ALLOWED_HOSTS="api.rodada.ai",
        DJANGO_CSRF_TRUSTED_ORIGINS="https://gerencia.rodada.ai")
    assert result.returncode == 0, result.stderr
    assert "security.W021" in result.stderr
    for code in ("security.W002", "security.W003", "security.W004", "security.W008", "security.W009"):
        assert code not in result.stderr
