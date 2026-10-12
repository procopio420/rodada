"""Explicit HTTP transport for Django's test client, including PostgreSQL CI."""

import pytest


@pytest.fixture(autouse=True)
def test_client_host_compatibility(settings):
    settings.RODADA_HOST_COMPATIBILITY_HOSTS = (
        *settings.RODADA_HOST_COMPATIBILITY_HOSTS,
        "testserver",
    )
