#!/usr/bin/env python3
"""Outbound-only local bridge. Run from the API Python environment; no inbound port."""

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))
from modules.documents_printing.adapters import (
    FileAdapter,
    NetworkAdapter,
    SpoolAdapter,
)


def api(base, token, path, data, allow_refresh=True):
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
        with urllib.request.urlopen(request, timeout=15) as response:
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
        with urllib.request.urlopen(refresh, timeout=15) as response:
            credentials = json.load(response)
        token.update(
            access_token=credentials["access_token"],
            refresh_token=credentials["refresh_token"],
        )
        # Only retry the fenced API command, never the adapter's physical submission.
        return api(base, token, path, data, allow_refresh=False)


def run_once(base, token, config):
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
    if not base.startswith("https://") and not base.startswith(
        ("http://127.0.0.1:", "http://localhost:")
    ):
        raise SystemExit("Use HTTPS outside loopback.")
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
