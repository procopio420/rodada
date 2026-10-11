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

    def __init__(self, address, handler, evidence):
        super().__init__(address, handler)
        self.lock = threading.Lock()
        self.armed = True
        self.events = []
        self.evidence = evidence

    def snapshot(self):
        return {"armed": self.armed, "events": self.events}

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
        headers["Host"] = "127.0.0.1:8101"
        conn = http.client.HTTPConnection("127.0.0.1", 8101, timeout=30)
        try:
            conn.request(method, self.path, body=body, headers=headers)
            upstream = conn.getresponse()
            response_body = upstream.read()  # upstream response => transaction committed
            status = upstream.status
            response_headers = upstream.getheaders()
            if method == "POST" and MATCH.fullmatch(urlsplit(self.path).path) and 200 <= status < 300:
                original = json.loads(body or b"{}")
                data = json.loads(response_body)
                event = {
                    "upstream_status": status,
                    "order_id": data["id"],
                    "tab_id": data["tab_id"],
                    "idempotency_key": original["idempotency_key"],
                    "body_sha256": hashlib.sha256(body or b"").hexdigest(),
                }
                with self.server.lock:
                    if self.server.armed:
                        self.server.events.append(event)
                        self.server.persist()
                        print(f"POST_COMMITTED_BUT_RESPONSE_DROPPED status={status} order_id={data['id']}", flush=True)
                        # A real TCP RST, not a successful HTTP response or fake JSON.
                        self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
                        self.connection.close()
                        self.close_connection = True
                        return
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
    args = parser.parse_args()
    app = Proxy(("0.0.0.0", 8000), Handler, args.evidence)
    app.persist()
    print("POST_DROP_PROXY_READY at :8000 => Django :8101", flush=True)
    app.serve_forever()


if __name__ == "__main__":
    main()
