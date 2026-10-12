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

@pytest.mark.parametrize("origin", [
    "https://user:secret@example.com", "https://example.com/api",
    "https://example.com?token=secret", "https://example.com#fragment",
    "http://localhost:8000.attacker.example", "http://example.com:8000",
    "https://example.com:bad", "https://example.com:0",
])
def test_unsafe_api_origin_cannot_send_credentials(origin):
    with patch("urllib.request.OpenerDirector.open") as send, pytest.raises(ValueError):
        bridge.api(origin, "test-secret", "bridge/claim/", {})
    send.assert_not_called()


@pytest.mark.parametrize("origin", ["https://api.example.com", "http://127.0.0.1:8000", "http://[::1]:8000"])
def test_api_origin_accepts_https_or_explicit_loopback(origin):
    assert bridge.validate_api_origin(origin) == origin


@pytest.mark.parametrize("redirect_refresh", [False, True])
def test_authenticated_command_refuses_real_http_redirect(redirect_refresh):
    import threading
    import urllib.error
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    received = []

    class Target(BaseHTTPRequestHandler):
        def do_POST(self):
            received.append(self.headers.get("Authorization"))
            self.send_response(204)
            self.end_headers()

        do_GET = do_POST

        def log_message(self, *args):
            pass

    target = ThreadingHTTPServer(("127.0.0.1", 0), Target)

    class Redirect(Target):
        def do_POST(self):
            if redirect_refresh and self.path.startswith("/printing/"):
                self.send_response(401)
                self.end_headers()
                return
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{target.server_port}/stolen")
            self.end_headers()

    source = ThreadingHTTPServer(("127.0.0.1", 0), Redirect)
    threads = [threading.Thread(target=server.serve_forever, daemon=True)
               for server in (target, source)]
    for thread in threads:
        thread.start()
    try:
        with pytest.raises(urllib.error.HTTPError) as error:
            bridge.api(
                f"http://127.0.0.1:{source.server_port}",
                {"access_token": "test-secret", "refresh_token": "test-refresh-secret"},
                "bridge/claim/", {},
            )
        assert error.value.code == 302
        assert received == []
    finally:
        for server in (source, target):
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join()
