#!/usr/bin/env python3
"""Outbound-only local bridge. Run from the API Python environment; no inbound port."""

import argparse
import base64
import ipaddress
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))
from modules.documents_printing.adapters import (
    FileAdapter,
    NetworkAdapter,
    SpoolAdapter,
)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_api_origin(base):
    try:
        parsed = urlsplit(base)
        port = parsed.port
    except (TypeError, ValueError) as error:
        raise ValueError("Invalid API origin") from error
    if (
        not parsed.hostname or parsed.username is not None or parsed.password is not None
        or parsed.path not in ("", "/") or parsed.query or parsed.fragment
        or any(character.isspace() for character in base)
        or (port is not None and not 1 <= port <= 65535)
    ):
        raise ValueError("Use a credential-free API origin")
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
        and port is not None
    ):
        raise ValueError("Use HTTPS outside explicit loopback")
    return base.rstrip("/")


def api(base, token, path, data, allow_refresh=True):
    base = validate_api_origin(base)
    opener = urllib.request.build_opener(NoRedirect())
    access = token["access_token"] if isinstance(token, dict) else token
    request = urllib.request.Request(
        base.rstrip("/") + "/printing/" + path,
        data=json.dumps(data).encode(),
        headers={
            "Authorization": "Bearer " + access,
            "Content-Type": "application/json",
        },
    )
    try:
        with opener.open(request, timeout=15) as response:
            return json.load(response) if response.status != 204 else None
    except urllib.error.HTTPError as error:
        if (
            error.code != 401
            or not allow_refresh
            or not isinstance(token, dict)
            or not token.get("refresh_token")
        ):
            raise
        refresh = urllib.request.Request(
            base.rstrip("/") + "/auth/refresh/",
            data=json.dumps({"refresh_token": token["refresh_token"]}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with opener.open(refresh, timeout=15) as response:
            credentials = json.load(response)
        token.update(
            access_token=credentials["access_token"],
            refresh_token=credentials["refresh_token"],
        )
        # Only retry the fenced API command, never the adapter's physical submission.
        return api(base, token, path, data, allow_refresh=False)


def validate_bridge_config(config):
    """Refuse unsafe printer destinations before any job is claimed.

    The bridge is designed for on-premises LAN/CUPS/file endpoints only.
    Credentials and print bytes must not be sent to public Internet printers.
    """
    if not isinstance(config, dict) or not isinstance(config.get("endpoints"), dict):
        raise ValueError("A local endpoints mapping is required")
    if not config["endpoints"]:
        raise ValueError("At least one local endpoint is required")
    trusted_networks = tuple(map(ipaddress.ip_network, (
        "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
        "127.0.0.0/8", "fc00::/7", "fe80::/10", "::1/128",
    )))
    for endpoint_id, destination in config["endpoints"].items():
        if not isinstance(endpoint_id, str) or not endpoint_id.strip():
            raise ValueError("Endpoint ID must be nonempty")
        if not isinstance(destination, dict):
            raise ValueError("Invalid local endpoint configuration")
        adapter = destination.get("adapter")
        if adapter not in {"FILE", "NETWORK", "SPOOL"}:
            raise ValueError("Only supported local print adapters are permitted")
        if not isinstance(destination.get("connection_ref"), str) or not destination["connection_ref"]:
            raise ValueError("An explicit connection_ref is required")
        if adapter == "NETWORK":
            host, port = destination.get("host"), destination.get("port", 9100)
            if not isinstance(host, str) or not host or host.strip() != host:
                raise ValueError("Network printer requires a fixed local host")
            try:
                address = ipaddress.ip_address(host)
                trusted = any(address in network for network in trusted_networks)
            except ValueError:
                trusted = bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*\.(?:local|lan)", host))
            if not trusted or type(port) is not int or not (1 <= port <= 65535):
                raise ValueError("Network printers must use private LAN hosts and valid ports")
        elif adapter == "SPOOL":
            queue = destination.get("queue")
            if not isinstance(queue, str) or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}", queue):
                raise ValueError("A safe local CUPS queue name is required")
        else:
            directory = destination.get("directory")
            if not isinstance(directory, str) or not directory.strip():
                raise ValueError("FILE endpoint requires an explicit output directory")
    return config


def run_once(base, token, config):
    validate_bridge_config(config)
    job = api(base, token, "bridge/claim/", {"endpoint_ids": list(config["endpoints"])})
    if not job:
        return False
    try:
        destination = config["endpoints"][job["endpoint_id"]]
        if (
            destination["adapter"] != job["adapter"]
            or destination["connection_ref"] != job["connection_ref"]
        ):
            outcome, detail = (
                "FAILED_FINAL",
                "Configuração local e endpoint divergem; envio bloqueado.",
            )
        else:
            if job["adapter"] == "FILE":
                adapter = FileAdapter(destination["directory"])
                payload = job["html"].encode()
            elif job["adapter"] == "NETWORK":
                adapter = NetworkAdapter(
                    destination["host"], destination.get("port", 9100)
                )
                payload = base64.b64decode(job["escpos"], validate=True)
            elif job["adapter"] == "SPOOL":
                adapter = SpoolAdapter(destination["queue"])
                payload = base64.b64decode(job["escpos"], validate=True)
            else:
                raise ValueError("Unsupported local adapter")
            result = adapter.deliver(job["id"], payload)
            outcome, detail = result.outcome, result.detail
    except Exception:  # noqa: BLE001 — unknown post-send errors must remain uncertain.
        # Unknown errors must never authorize a resend after possible side effects.
        outcome, detail = (
            "DELIVERY_UNCERTAIN",
            "Bridge interrompido; verificar destino antes de reimprimir.",
        )
    # If this request fails, do NOT resend bytes. Lease recovery makes the job uncertain.
    api(
        base,
        token,
        "bridge/jobs/" + job["id"] + "/result/",
        {"attempt_token": job["attempt_token"], "outcome": outcome, "detail": detail},
    )
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    base = os.environ["RODADA_PRINT_API_URL"]
    token = {
        "access_token": os.environ["RODADA_PRINT_ACCESS_TOKEN"],
        "refresh_token": os.environ.get("RODADA_PRINT_REFRESH_TOKEN", ""),
    }
    validate_api_origin(base)
    while True:
        try:
            active = run_once(base, token, config)
        except urllib.error.HTTPError as error:
            if error.code in (401, 403):
                raise SystemExit(
                    "Sessão do bridge expirada/revogada; autentique novamente."
                )
            print(
                "API indisponível; nenhum reenvio automático de dados.", file=sys.stderr
            )
            active = False
        except (OSError, ValueError):
            print(
                "Conexão indisponível; trabalhos permanecem no servidor.",
                file=sys.stderr,
            )
            active = False
        if args.once:
            return
        time.sleep(1 if active else 5)


if __name__ == "__main__":
    main()
