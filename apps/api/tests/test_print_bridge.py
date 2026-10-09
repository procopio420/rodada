"""Local outbound bridge behavior without physical devices or external API calls."""

import importlib.util
import json
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

spec = importlib.util.spec_from_file_location(
    "rodada_print_bridge",
    Path(__file__).resolve().parents[3] / "tools" / "print-bridge" / "bridge.py",
)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def test_lost_result_ack_never_resubmits_adapter_bytes():
    job = {
        "id": "11111111-1111-4111-8111-111111111111",
        "endpoint_id": "file",
        "adapter": "FILE",
        "connection_ref": "local",
        "html": "<html>receipt</html>",
        "attempt_token": "token",
    }
    config = {
        "endpoints": {
            "file": {"adapter": "FILE", "connection_ref": "local", "directory": "/unused"}
        }
    }
    with (
        patch.object(bridge, "api", side_effect=[job, OSError("offline")]),
        patch.object(
            bridge.FileAdapter,
            "deliver",
            return_value=MagicMock(outcome="OUTPUT_READY", detail="file ready"),
        ) as deliver,
    ):
        import pytest

        with pytest.raises(OSError):
            bridge.run_once("https://example.invalid", "token", config)
        deliver.assert_called_once()


def test_refresh_rotates_only_api_credentials_in_memory():
    credentials = {"access_token": "old-access", "refresh_token": "old-refresh"}
    refreshed = MagicMock()
    refreshed.__enter__.return_value.read.return_value = json.dumps(
        {"access_token": "new-access", "refresh_token": "new-refresh"}
    ).encode()
    accepted = MagicMock()
    accepted.__enter__.return_value.status = 204
    error = urllib.error.HTTPError("https://example.invalid", 401, "expired", {}, None)
    with patch("urllib.request.urlopen", side_effect=[error, refreshed, accepted]) as request:
        assert (
            bridge.api(
                "https://example.invalid", credentials, "bridge/claim/", {"endpoint_ids": ["file"]}
            )
            is None
        )
        assert credentials["access_token"] == "new-access"
        assert credentials["refresh_token"] == "new-refresh"
        assert request.call_count == 3
