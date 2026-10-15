"""Disposable, database-free ASGI transport fixture; never connects to Rodada."""
import json
import socket

import uvicorn

requests = []


async def app(scope, receive, send):
    body = bytearray()
    while True:
        message = await receive()
        if message["type"] == "http.disconnect":
            return
        body.extend(message.get("body", b""))
        if not message.get("more_body", False):
            break
    path = scope["path"]
    if path == "/stats":
        payload = requests
    else:
        requests.append({"path": path, "method": scope["method"], "body": body.decode(), "content_length": dict(scope["headers"]).get(b"content-length", b"").decode()})
        payload = {"code": "VENUE_HOST_NOT_FOUND"} if path == "/reject" else {"body": body.decode()}
    status = {"/reject": 421, "/forbidden": 403, "/redirect": 307}.get(path, 200)
    headers = [(b"content-type", b"application/json")]
    if path == "/redirect":
        headers.append((b"location", b"/ok"))
    await send({"type": "http.response.start", "status": status, "headers": headers})
    if path == "/stream":
        await send({"type": "http.response.body", "body": b"first\n", "more_body": True})
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
    else:
        await send({"type": "http.response.body", "body": json.dumps(payload).encode()})


if __name__ == "__main__":
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    print(f"LISTENING {listener.getsockname()[1]}", flush=True)
    uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="off")).run(sockets=[listener])
