"""Outbound HTTPS JSON. No redirects, staff login, cookies or URL secrets."""

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class AgentHttpError(Exception):
    def __init__(self, status: int):
        self.status = status
        super().__init__(f"API status {status}")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        return None


def validate_origin(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    if (
        parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
        or not parsed.hostname
    ):
        raise ValueError("Credential-free API origin required.")
    if parsed.scheme != "https" and not (
        parsed.scheme == "http"
        and parsed.hostname in ("127.0.0.1", "localhost", "::1")
        and parsed.port is not None
    ):
        raise ValueError("HTTPS required; development HTTP is loopback-only with explicit port.")
    return value.rstrip("/")


class AgentApi:
    def __init__(self, origin: str):
        self.origin = validate_origin(origin)
        self.opener = urllib.request.build_opener(NoRedirect())

    def post(self, path: str, body: dict[str, Any], token: str = "") -> dict[str, Any]:
        if path not in (
            "pairing/start/",
            "pairing/status/",
            "me/activate/",
            "me/heartbeat/",
            "me/discovery/",
            "me/claim/",
        ) and not re.fullmatch(r"me/jobs/[0-9a-f-]{36}/result/", path):
            raise ValueError("Protocol-relative API path required.")
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        request = urllib.request.Request(
            self.origin + "/printing/agents/v1/" + path,
            json.dumps(body).encode(),
            headers,
            method="POST",
        )
        try:
            with self.opener.open(request, timeout=8) as response:
                raw = response.read(524289)
                if len(raw) > 524288:
                    raise ValueError("API response exceeds limit.")
                result = json.loads(raw)
        except urllib.error.HTTPError as exc:
            raise AgentHttpError(exc.code) from None
        if not isinstance(result, dict):
            raise TypeError("Invalid API response.")
        return result
