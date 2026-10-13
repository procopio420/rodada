#!/usr/bin/env python3
"""Fast, dependency-free checks for agent guidance and active domain documents.

Scope is deliberately small: validates internal Markdown file references and
canonical hostnames, NOT feature implementation, ADR semantics or deployment.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
GUIDANCE = (
    "AGENTS.md",
    "apps/api/AGENTS.md",
    "apps/web/AGENTS.md",
    "apps/attendance-android/AGENTS.md",
    "docs/architecture/tenant-routing-contract.md",
    "docs/adr/0018-rodada-bar-canonical-domain.md",
    "specs/025-tenant-host-routing/spec.md",
    "specs/025-tenant-host-routing/acceptance.md",
)
CURRENT_DOMAIN_DOCS = (
    "README.md",
    "apps/web/README.md",
    "docs/architecture/tenant-routing-contract.md",
)


def guidance_files(root: Path) -> list[Path]:
    paths = [root / item for item in GUIDANCE]
    paths.extend(sorted((root / "docs" / "agents").glob("*.md")))
    return paths


def _local_link_target(source: Path, url: str) -> Path | None:
    # Handle Markdown's optional title: (../path "Title").
    raw = url.strip()
    if raw.startswith("<") and ">" in raw:
        raw = raw[1 : raw.index(">")]
    else:
        raw = raw.split(None, 1)[0]
    if not raw or raw.startswith("#"):
        return None
    parsed = urlsplit(raw)
    if parsed.scheme or parsed.netloc or raw.startswith("//"):
        return None
    path = unquote(parsed.path)
    if not path:
        return None
    return source.parent / path


def check_links(root: Path, paths: list[Path] | None = None) -> tuple[list[str], int]:
    errors: list[str] = []
    checked = 0
    root = root.resolve()
    for source in paths if paths is not None else guidance_files(root):
        if not source.is_file():
            errors.append(f"{source}: required guidance file missing")
            continue
        try:
            content = source.read_text(encoding="utf-8")
        except UnicodeError:
            errors.append(f"{source}: not valid UTF-8")
            continue
        for match in LINK_RE.finditer(content):
            target = _local_link_target(source, match.group(1))
            if target is None:
                continue
            checked += 1
            target = target.resolve()
            if not target.is_relative_to(root):
                errors.append(f"{source}: link escapes repository: {match.group(1)}")
            elif not target.exists():
                errors.append(f"{source}: broken local link: {match.group(1)}")
    return errors, checked


def check_canonical_domains(root: Path) -> list[str]:
    errors: list[str] = []
    for name in CURRENT_DOMAIN_DOCS:
        path = root / name
        if not path.is_file():
            errors.append(f"{name}: active domain contract missing")
            continue
        content = path.read_text(encoding="utf-8")
        if "rodada.ai" in content:
            errors.append(f"{name}: historical rodada.ai found in active contract; move history to ADR")
        if "rodada.bar" not in content:
            errors.append(f"{name}: canonical rodada.bar is missing")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    errors, checked = check_links(root)
    errors += check_canonical_domains(root)
    if errors:
        print("\n".join(f"ERROR {error}" for error in errors), file=sys.stderr)
        print(f"KB check failed: {len(errors)} errors, {checked} links checked", file=sys.stderr)
        return 1
    print(f"KB check PASS: {len(guidance_files(root))} documents, {checked} links, canonical rodada.bar")
    print("Note: this is NOT a spec acceptance, CI implementation gate or deployed-domain check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
