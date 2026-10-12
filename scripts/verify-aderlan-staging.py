#!/usr/bin/env python3
"""Read-only gate for the *isolated* Aderlan staging/demo Web surface.

No login, seed, mutation, provider operation or claim about live merchant state.
By default only loopback may be tested; an exact demo hostname is opt-in.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler


PAGES = ("staff", "attendance", "bar", "kitchen", "manage", "cash", "reports")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def allow_target(base, public_demo):
    parsed = urlparse(base)
    if parsed.query or parsed.fragment or parsed.username or parsed.password or parsed.path not in ("", "/"):
        raise ValueError("Use an origin, without credentials, paths or query parameters")
    if parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost", "::1"):
        return parsed.geturl().rstrip("/")
    if public_demo and parsed.scheme == "https" and parsed.hostname == "rodada-web-demo.up.railway.app":
        return parsed.geturl().rstrip("/")
    raise ValueError("Only loopback or the explicitly permitted HTTPS Aderlan demo is testable")


def probe(base, page):
    url = base + "/" + page
    request = Request(url, headers={"User-Agent": "Rodada-Staging-Readiness/1.0"}, method="GET")
    try:
        with build_opener(NoRedirect()).open(request, timeout=15) as response:
            status = response.status
            headers = response.headers
            content = response.read(64_000)
    except HTTPError as error:
        status, headers, content = error.code, error.headers, b""
    except (URLError, TimeoutError, OSError) as error:
        return {"path": "/" + page, "passed": False, "reason": type(error).__name__}
    media_type = headers.get_content_type().lower()
    passed = status == 200 and media_type == "text/html" and bool(content.strip())
    return {
        "path": "/" + page,
        "http_status": status,
        "content_type": media_type,
        "passed": passed,
        "reason": "ok" if passed else "Route must respond with nonempty HTML/HTTP 200 without redirect",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:18080")
    parser.add_argument("--public-demo", action="store_true",
                        help="Read-only validation of the exact existing Railway demo domain")
    parser.add_argument("--evidence", help="Save non-sensitive JSON report at this path")
    args = parser.parse_args(argv)
    try:
        base = allow_target(args.base, args.public_demo)
    except ValueError as error:
        parser.error(str(error))
    results = [probe(base, page) for page in PAGES]
    summary = {
        "kind": "staging-web-routes-read-only",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "target": base,
        "results": results,
        "passed": all(result["passed"] for result in results),
        "limitations": [
            "Does not authenticate users or submit orders",
            "Does not verify actual Railway deployment SHA or database correctness",
            "Does not authorize a venue to replace its incumbent POS",
        ],
    }
    if args.evidence:
        from pathlib import Path
        out = Path(args.evidence)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
