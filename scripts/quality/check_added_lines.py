#!/usr/bin/env python3
"""Fail only on newly added Ruff diagnostics or Web unsafe directives.

Entire pre-existing Python source is still audited and its debt counted.
Checks compare BASE_SHA to the current checkout (a PR merge ref is supported).
No network, secret access, install or write side effects.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
WEB_EXTS = (".ts", ".tsx", ".js", ".jsx", ".mjs")
WEB_RULES = (
    ("TYPECHECK_BYPASS", re.compile(r"@ts-(?:ignore|nocheck)\b")),
    ("LINT_BYPASS", re.compile(r"eslint-disable\b")),
    ("DYNAMIC_CODE", re.compile(r"\beval\s*\(|\bnew\s+Function\s*\(")),
    ("BROWSER_SECRET", re.compile(
        r"process\.env\.NEXT_PUBLIC_[A-Z_]*(?:SECRET|PRIVATE|PASSWORD|TOKEN|PIN|SIGNING_KEY)\b"
    )),
    ("TOKEN_IN_BROWSER_STORAGE", re.compile(
        r"(?:localStorage|sessionStorage)\s*\.\s*(?:setItem|getItem)\s*\("
        r".*(?:access_token|refresh_token|auth_token|private_key)"
    )),
)


def added_lines(diff: str) -> tuple[dict[str, set[int]], dict[str, dict[int, str]]]:
    """Parse zero-context diff without executing content from the diff."""
    result: dict[str, set[int]] = {}
    text: dict[str, dict[int, str]] = {}
    path: str | None = None
    line = 0
    in_hunk = False
    for record in diff.splitlines():
        if record.startswith("+++ b/"):
            path = record[6:]
            in_hunk = False
            result.setdefault(path, set())
            text.setdefault(path, {})
        elif record.startswith("+++ /dev/null"):
            path = None
            in_hunk = False
        elif record.startswith("@@ "):
            match = HUNK.match(record)
            if match and path is not None:
                line = int(match.group(1))
                in_hunk = True
            else:
                in_hunk = False
        elif in_hunk and path is not None:
            if record.startswith("+"):
                result[path].add(line)
                text[path][line] = record[1:]
                line += 1
            elif record.startswith(" "):
                line += 1
            elif record.startswith("\\ No newline"):
                continue
            # deleted lines do not increment the new-file line number
    return result, text


def web_findings(lines: dict[str, dict[int, str]]) -> list[str]:
    errors = []
    for path, additions in sorted(lines.items()):
        if not path.startswith("apps/web/") or not path.endswith(WEB_EXTS):
            continue
        for row, source in sorted(additions.items()):
            for rule, pattern in WEB_RULES:
                if pattern.search(source):
                    errors.append(f"{path}:{row}: {rule}: risky new source directive")
    return errors


def ruff_findings(
    diagnostics: list[dict], additions: dict[str, set[int]], root: Path
) -> list[str]:
    errors = []
    for item in diagnostics:
        path = Path(item["filename"])
        try:
            name = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            continue
        row = item["location"]["row"]
        if row in additions.get(name, set()):
            errors.append(f"{name}:{row}: {item['code']}: {item['message']}")
    return errors


def run(args: argparse.Namespace) -> int:
    root = Path(__file__).resolve().parents[2]
    diff = subprocess.run(
        ["git", "diff", "--no-ext-diff", "--unified=0", "--no-renames",
         args.base, "HEAD", "--", "apps/api", "apps/web"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    if diff.returncode:
        print(f"ERROR git diff failed: {diff.stderr.strip()}", file=sys.stderr)
        return 2
    additions, source = added_lines(diff.stdout)
    if args.kind == "web":
        errors = web_findings(source)
        print(f"Web added-line guard: {sum(len(v) for k, v in additions.items() if k.startswith('apps/web/'))} added lines checked; {len(errors)} findings")
    else:
        process = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "apps/api", "--output-format", "json",
             "--select", "E4,E7,E9,F"],
            cwd=root, capture_output=True, text=True, check=False,
        )
        if process.returncode not in (0, 1):
            print(f"ERROR Ruff failed: {process.stderr.strip()}", file=sys.stderr)
            return 2
        try:
            diagnostics = json.loads(process.stdout)
        except json.JSONDecodeError:
            print("ERROR Ruff produced invalid diagnostic JSON", file=sys.stderr)
            return 2
        errors = ruff_findings(diagnostics, additions, root)
        print(f"Ruff full-source audit: {len(diagnostics)} findings (existing + new); "
              f"{len(errors)} findings on added lines")
        print("Legacy diagnostics are visible as counts; new violations block CI.")
    for error in errors[:80]:
        print("ERROR " + error, file=sys.stderr)
    if len(errors) > 80:
        print(f"... and {len(errors)-80} more findings", file=sys.stderr)
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Trusted base commit SHA")
    parser.add_argument("--kind", choices=("api", "web"), required=True)
    args = parser.parse_args()
    if not re.fullmatch("[0-9a-fA-F]{7,40}", args.base):
        parser.error("--base must be a git commit SHA")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
