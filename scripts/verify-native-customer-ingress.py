#!/usr/bin/env python3
"""Nonfinancial ingress contract probes; run only against a disposable local image."""

import argparse
import json
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    base = args.base.rstrip("/")
    if urlsplit(base).hostname not in {"localhost", "127.0.0.1"}:
        parser.error("Only a disposable loopback image is supported")
    bodies = {
        "register": {
            "username": "ingress-ci-profile",
            "password": "ci-disposable-passphrase",
            "display_name": "Fictional ingress fixture",
        },
        "login": {
            "username": "ingress-ci-profile",
            "password": "ci-disposable-passphrase",
        },
        "context": None,
        "claim": {"target_tab_id": "00000000-0000-0000-0000-000000000000"},
        "logout": {},
        "password": {
            "old_password": "ci-disposable-passphrase",
            "new_password": "new-ci-disposable-passphrase",
        },
    }
    for forged in (False, True):
        for action, body in bodies.items():
            path = f"/guest/customer/{action}/"
            headers = {"Host": "api.rodada.bar", "Content-Type": "application/json"}
            if forged:
                headers.update(
                    {
                        "X-Forwarded-Host": "e2ea.rodada.bar",
                        "X-Rodada-Bff-Host": "e2ea.rodada.bar",
                        "X-Rodada-Bff-Time": "0",
                        "X-Rodada-Bff-Signature": "0" * 64,
                    }
                )
            request = Request(
                base + path,
                data=json.dumps(body).encode() if body is not None else None,
                headers=headers,
            )
            try:
                response = urlopen(request, timeout=20)
            except HTTPError as error:
                response = error
            with response:
                status = response.status
                payload = json.load(response)
            assert status == 401 and payload.get("code") == "GUEST_SESSION_REQUIRED", (
                action,
                forged,
                status,
            )
            print(f"PASS native customer/{action}: JSON401, forged_assertion={forged}")


if __name__ == "__main__":
    main()
