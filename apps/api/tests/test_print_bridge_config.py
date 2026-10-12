"""Printer bridge preflight: no network or printer device is contacted."""
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

spec = importlib.util.spec_from_file_location(
    "rodada_print_bridge_config",
    Path(__file__).resolve().parents[3] / "tools" / "print-bridge" / "bridge.py",
)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def config(adapter="NETWORK", **options):
    return {"endpoints": {"test-printer": {
        "adapter": adapter, "connection_ref": "local-station", **options,
    }}}


@pytest.mark.parametrize("host", [
    "8.8.8.8", "1.1.1.1", "printer.example.com",
    "metadata.google.internal", "169.254.169.254",
    "0.0.0.0", "printer.local.example.com",
])
def test_public_destinations_are_refused_before_claim(host):
    destination = config(host=host, port=9100)
    with patch.object(bridge, "api") as api, pytest.raises(ValueError):
        bridge.run_once("http://localhost:8000", "fake", destination)
    api.assert_not_called()


@pytest.mark.parametrize("host", ["192.168.1.80", "10.0.0.8", "172.16.4.50",
                                  "printer.local", "bar-printer.lan", "127.0.0.1"])
def test_private_destinations_can_be_configured_without_network(host):
    destination = config(host=host, port=9100)
    assert bridge.validate_bridge_config(destination) is destination


@pytest.mark.parametrize("port", [0, -1, 65536, "9100", True])
def test_invalid_ports_are_refused(port):
    with pytest.raises(ValueError):
        bridge.validate_bridge_config(config(host="192.168.1.80", port=port))


def test_unsafe_spool_queue_is_refused():
    with pytest.raises(ValueError):
        bridge.validate_bridge_config(config(adapter="SPOOL", queue="--help"))
    assert bridge.validate_bridge_config(config(adapter="SPOOL", queue="rodada_bar"))


def test_missing_or_unsupported_config_blocks_job_claim():
    with patch.object(bridge, "api") as api:
        for candidate in ({}, {"endpoints": {}}, config(adapter="REMOTE")):
            with pytest.raises(ValueError):
                bridge.run_once("http://localhost:8000", "fake", candidate)
        api.assert_not_called()


def test_local_file_adapter_does_not_require_hardware():
    assert bridge.validate_bridge_config(
        config(adapter="FILE", directory="/tmp/rodada-printer-acceptance")
    )
