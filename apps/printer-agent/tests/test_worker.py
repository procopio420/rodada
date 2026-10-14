import copy
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from rodada_printer_agent.client import AgentApi, AgentHttpError, validate_origin
from rodada_printer_agent.worker import InstallationState, Worker


class Store:
    def __init__(self):
        self.state = InstallationState()
        self.public = {}

    def load(self):
        return copy.deepcopy(self.state)

    def save(self, state):
        self.state = copy.deepcopy(state)

    def diagnostic(self, data):
        self.public = data


class Api:
    def __init__(self):
        self.calls = []
        self.approved = False
        self.failure = None
        self.raw = "rpa_" + "t" * 43

    def post(self, path, body, token=""):
        self.calls.append((path, body, token))
        if self.failure:
            raise self.failure
        if path == "pairing/start/":
            return {"request_id": "request", "code": "A" * 16, "expires_at": "future"}
        if path == "pairing/status/":
            return (
                {"state": "APPROVED", "credential": self.raw}
                if self.approved
                else {"state": "PENDING_PAIRING"}
            )
        if path == "me/activate/":
            return {"state": "PAIRED"}
        return {"protocol_version": 1, "delivery_enabled": False}


def test_restart_pair_activation_and_revocation_do_not_store_staff_or_print():
    store, api = Store(), Api()
    worker = Worker(store, api)
    installation = store.state.installation_id
    proof = store.state.proof
    worker.tick("Synthetic PC")
    assert store.public["state"] == "PENDING_PAIRING"
    assert store.state.proof == proof
    api.approved = True
    Worker(store, api).tick("Synthetic PC")
    assert store.state.installation_id == installation
    assert store.state.credential == api.raw and store.state.proof == ""
    assert api.raw not in json.dumps(store.public)
    assert proof not in json.dumps(store.public)
    api.failure = AgentHttpError(401)
    worker = Worker(store, api)
    worker.tick("Synthetic PC")
    assert store.state.authorization_lost and store.state.credential == ""
    calls = len(api.calls)
    Worker(store, api).tick("Synthetic PC")
    assert len(api.calls) == calls
    assert all("claim" not in path and "staff" not in path for path, _, _ in api.calls)


def test_offline_and_disabled_venue_preserve_identity_and_credential():
    store, api = Store(), Api()
    api.approved = True
    Worker(store, api).tick("PC")
    for error in (OSError("Synthetic offline"), AgentHttpError(403), AgentHttpError(503)):
        api.failure = error
        Worker(store, api).tick("PC")
        assert store.state.credential == api.raw
        assert not store.state.authorization_lost


def test_lost_activation_ack_retries_without_losing_persisted_credential():
    store, api = Store(), Api()
    api.approved = True
    original = api.post

    def lost(path, body, token=""):
        if path == "me/activate/":
            raise OSError("Synthetic response lost")
        return original(path, body, token)

    api.post = lost
    Worker(store, api).tick("PC")
    assert store.state.credential == api.raw and not store.state.activated
    api.post = original
    Worker(store, api).tick("PC")
    assert store.state.activated
    assert sum(path == "pairing/status/" for path, _, _ in api.calls) == 1


@pytest.mark.parametrize(
    "url",
    [
        "http://api.example",
        "https://u:p@api.example",
        "https://api.example/?secret=x",
        "https://api.example/path",
        "https://api.example/#x",
    ],
)
def test_unsafe_api_origin_denied(url):
    with pytest.raises(ValueError):
        validate_origin(url)


def test_redirect_never_forwards_credential():
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            calls.append(self.path)
            self.send_response(302)
            self.send_header("Location", "/credential-destination")
            self.end_headers()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        api = AgentApi(f"http://127.0.0.1:{server.server_port}")
        with pytest.raises(AgentHttpError) as error:
            api.post("me/heartbeat/", {}, "rpa_" + "t" * 43)
        assert error.value.status == 302
        assert calls == ["/printing/agents/v1/me/heartbeat/"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_failed_credential_persistence_never_acknowledges_activation():
    store, api = Store(), Api()
    worker = Worker(store, api)
    api.approved = True
    save = store.save

    def failed(state):
        if state.credential:
            raise OSError("Synthetic disk full")
        save(state)

    store.save = failed
    worker.tick("PC")
    worker.tick("PC")
    assert not store.state.credential
    assert not any(path == "me/activate/" for path, _, _ in api.calls)
    store.save = save
    worker.tick("PC")
    assert store.state.credential == api.raw and store.state.activated


def test_expired_pending_retries_but_paired_conflict_pauses():
    store, api = Store(), Api()
    worker = Worker(store, api)
    worker.tick("PC")
    api.failure = AgentHttpError(410)
    worker.tick("PC")
    assert not store.state.request_id and store.public["state"] == "PAIRING_RETRY"
    api.failure = AgentHttpError(409)
    worker.tick("PC")
    assert store.state.authorization_lost
    calls = len(api.calls)
    worker.tick("PC")
    assert len(api.calls) == calls
