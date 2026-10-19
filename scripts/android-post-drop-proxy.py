#!/usr/bin/env python3
"""Disposable CI fault proxy: RESET Android TCP response after Django committed.

All upstream traffic is real HTTP to PostgreSQL-backed Django. Nothing is mocked.
The *first* successful order confirmation response is deliberately never delivered
to the Android client; if HttpURLConnection retries internally, every attempt is
dropped until the runner disarms the fault. Do not use outside an isolated test.
"""
import argparse
import hashlib
import http.client
import json
import os
import re
import socket
import struct
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

MATCH = re.compile(r"^/tabs/[0-9a-fA-F-]+/orders/confirm/$")
HOP = {"connection", "content-length", "transfer-encoding", "host", "keep-alive",
       "proxy-authorization", "proxy-authenticate", "upgrade", "te", "trailer"}


class Proxy(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, handler, evidence, hold_response=False, upstream_port=8101):
        super().__init__(address, handler)
        self.upstream_port = upstream_port
        self.lock = threading.Lock()
        self.armed = True
        self.mode = "order"
        self.events = []
        self.replays = []
        self.evidence = evidence
        self.hold_response = hold_response
        self.holding = 0
        self.release_signal = threading.Event()
        self.release_after_cut = False
        self.read_path = None
        self.read_holding = False
        self.read_release = threading.Event()

    def snapshot(self):
        return {"mode": self.mode, "armed": self.armed, "events": self.events, "replays": self.replays,
                "hold_response": self.hold_response, "holding": self.holding,
                "released_after_cut": self.release_after_cut, "read_path": self.read_path, "read_holding": self.read_holding}

    def persist(self):
        parent = os.path.dirname(self.evidence) or "."
        with tempfile.NamedTemporaryFile("w", dir=parent, delete=False, encoding="utf-8") as temp:
            json.dump(self.snapshot(), temp, sort_keys=True)
            name = temp.name
        os.replace(name, self.evidence)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        if self.path == "/__fault/status":
            with self.server.lock:
                result = json.dumps(self.server.snapshot()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(result)))
            self.end_headers()
            self.wfile.write(result)
            return
        self.proxy("GET")

    def do_POST(self):
        held = re.fullmatch(r"/__fault/hold-tab-read/([0-9a-fA-F-]+)", self.path)
        if held or self.path == "/__fault/release-tab-read":
            with self.server.lock:
                if held:
                    self.server.read_path = f"/tabs/{held.group(1)}/"
                    self.server.read_holding = False
                    self.server.read_release.clear()
                else:
                    self.server.read_path = None
                    self.server.read_release.set()
                self.server.persist()
            payload = b'{"ok":true}'
            self.send_response(200)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path == "/__fault/release-after-cut":
            with self.server.lock:
                if not self.server.hold_response or not self.server.holding:
                    self.send_error(409, "No committed response is being held")
                    return
                self.server.release_after_cut = True
                self.server.persist()
                self.server.release_signal.set()
            payload = b'{"released_after_cut":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path in ("/__fault/arm-table-start", "/__fault/arm-table-open", "/__fault/arm-payment", "/__fault/arm-close"):
            with self.server.lock:
                self.server.mode = {"/__fault/arm-table-start": "start", "/__fault/arm-table-open": "open",
                                    "/__fault/arm-payment": "payment", "/__fault/arm-close": "close"}[self.path]
                self.server.armed = True
                self.server.events = []
                self.server.replays = []
                self.server.persist()
            payload = b'{"armed":true}'
            self.send_response(200)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path == "/__fault/disarm":
            with self.server.lock:
                if not self.server.events:
                    self.send_error(409, "No committed order response was dropped")
                    return
                self.server.armed = False
                self.server.persist()
            payload = b'{"armed":false}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self.proxy("POST")

    def proxy(self, method):
        size = int(self.headers.get("Content-Length", "0"))
        if not 0 <= size <= 1_048_576:
            self.send_error(413)
            return
        body = self.rfile.read(size) if size else None
        headers = {key: value for key, value in self.headers.items() if key.lower() not in HOP}
        headers["Host"] = f"127.0.0.1:{self.server.upstream_port}"
        conn = http.client.HTTPConnection("127.0.0.1", self.server.upstream_port, timeout=30)
        try:
            conn.request(method, self.path, body=body, headers=headers)
            upstream = conn.getresponse()
            if method == "GET" and self.path.startswith("/realtime/stream/"):
                self.send_response(upstream.status)
                for key, value in upstream.getheaders():
                    if key.lower() not in HOP:
                        self.send_header(key, value)
                self.send_header("Connection", "close")
                self.end_headers()
                while True:
                    line = upstream.readline()
                    if not line:
                        break
                    self.wfile.write(line)
                    self.wfile.flush()
                self.close_connection = True
                return
            response_body = upstream.read()  # upstream response => transaction committed
            status = upstream.status
            response_headers = upstream.getheaders()
            mode = self.server.mode
            route = urlsplit(self.path).path
            hold_read = method == "GET" and route == self.server.read_path and 200 <= status < 300
            if hold_read:
                with self.server.lock:
                    self.server.read_holding = True
                    self.server.persist()
                # Return only this actual canonical snapshot after the session test releases it.
                if not self.server.read_release.wait(timeout=45):
                    raise TimeoutError("Disposable Tab read barrier timed out")
                with self.server.lock:
                    self.server.read_holding = False
                    self.server.persist()
            pattern = {"order": MATCH.pattern,
                       "start": r"/hospitality/tables/[0-9a-fA-F-]+/service/start/",
                       "open": r"/hospitality/occupancies/[0-9a-fA-F-]+/tabs/open/",
                       "payment": r"/tabs/[0-9a-fA-F-]+/payments/",
                       "close": r"/tabs/[0-9a-fA-F-]+/close/"}[mode]
            matches = re.fullmatch(pattern, route)
            if method == "POST" and matches and 200 <= status < 300:
                original = json.loads(body or b"{}")
                data = json.loads(response_body)
                event = {
                    "upstream_status": status,
                    "mode": mode,
                    "path": route,
                    "order_id": data.get("id"),
                    "tab_id": data.get("tab_id"),
                    "table_id": data.get("table_id"),
                    "occupancy_id": data.get("occupancy_id") or data.get("active_occupancy", {}).get("id"),
                    "idempotency_key": original.get("idempotency_key"),
                    "body_sha256": hashlib.sha256(body or b"").hexdigest(),
                }
                with self.server.lock:
                    if self.server.armed:
                        self.server.events.append(event)
                        self.server.persist()
                        print(f"POST_COMMITTED_BUT_RESPONSE_DROPPED status={status} mode={mode}", flush=True)
                        if self.server.hold_response:
                            self.server.holding += 1
                            self.server.persist()
                        else:
                            # Existing test: a real TCP RST, never a fake successful HTTP response.
                            self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
                            self.connection.close()
                            self.close_connection = True
                            return
                if self.server.armed and self.server.hold_response:
                    # The caller is blocked inside a real HTTP POST until the test
                    # runner cuts the Android network. No response is sent before that.
                    if not self.server.release_signal.wait(timeout=20):
                        print("HOLD_RESPONSE_TIMEOUT", flush=True)
                        self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
                        self.connection.close()
                        self.close_connection = True
                        return
                    with self.server.lock:
                        if not self.server.release_after_cut:
                            raise RuntimeError("Held response released without verified network cut")
                    print("RELEASING_COMMITTED_RESPONSE_AFTER_ANDROID_NETWORK_CUT", flush=True)
                    # Attempt delivery of the genuine upstream HTTP response only
                    # after the Android uplink has been disconnected.
                    # A client-side IOException, not this log alone, proves loss.
                    self.send_response(status)
                    for name, value in response_headers:
                        if name.lower() not in HOP:
                            self.send_header(name, value)
                    self.send_header("Content-Length", str(len(response_body)))
                    self.end_headers()
                    self.wfile.write(response_body)
                    return
                if not self.server.armed:
                    with self.server.lock:
                        self.server.replays.append(event)
                        self.server.persist()
            self.send_response(status)
            for name, value in response_headers:
                if name.lower() not in HOP:
                    self.send_header(name, value)
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)
        except (OSError, http.client.HTTPException) as exc:
            print(f"UPSTREAM_FAILED: {type(exc).__name__}: {exc}", flush=True)
            try:
                self.send_error(502, "Test backend unavailable")
            except OSError:
                pass
        finally:
            conn.close()

    def log_message(self, format, *args):
        # Avoid printing Authorization or request JSON (session and PIN).
        return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--listen-port", type=int, default=8000)
    parser.add_argument("--upstream-port", type=int, default=8101)
    parser.add_argument("--hold-response", action="store_true",
                        help="Pause a committed POST until externally verified Android uplink cut")
    args = parser.parse_args()
    app = Proxy(("0.0.0.0", args.listen_port), Handler, args.evidence, hold_response=args.hold_response, upstream_port=args.upstream_port)
    app.persist()
    print(f"POST_DROP_PROXY_READY hold_response={args.hold_response} at :{args.listen_port} => Django :{args.upstream_port}", flush=True)
    app.serve_forever()


if __name__ == "__main__":
    main()
