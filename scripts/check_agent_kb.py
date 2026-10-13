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
    "apps/landing/AGENTS.md",
    "docs/architecture/tenant-routing-contract.md",
    "docs/adr/0018-rodada-bar-canonical-domain.md",
    "specs/025-tenant-host-routing/spec.md",
    "specs/025-tenant-host-routing/acceptance.md",
)
SKILL_ROOTS = (".agents/skills", ".claude/skills")
REQUIRED_SKILLS = (
    "rodada-django-api",
    "rodada-nextjs-web",
    "rodada-static-html",
    "rodada-ui-design",
    "rodada-android-compose",
    "rodada-pos-safety",
)
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"\A---\n(?P<header>.*?)\n---\n", re.DOTALL)

CURRENT_DOMAIN_DOCS = (
    "README.md",
    "apps/web/README.md",
    "docs/architecture/tenant-routing-contract.md",
)


def guidance_files(root: Path) -> list[Path]:
    paths = [root / item for item in GUIDANCE]
    paths.extend(sorted((root / "docs" / "agents").glob("*.md")))
    for folder in SKILL_ROOTS:
        paths.extend(sorted((root / folder).glob("*/SKILL.md")))
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


def check_skill_manifests(
    root: Path, expected_names: tuple[str, ...] = REQUIRED_SKILLS
) -> list[str]:
    """Validate minimal Agent Skills front matter and Claude entrypoint mapping."""
    errors: list[str] = []
    for folder in SKILL_ROOTS:
        base = root / folder
        actual = {p.parent.name for p in base.glob("*/SKILL.md")}
        if extra := actual.difference(expected_names):
            errors.append(f"{base}: unregistered skill(s): {', '.join(sorted(extra))}")
        for name in expected_names:
            path = base / name / "SKILL.md"
            if not path.is_file():
                errors.append(f"{path}: missing required skill")
                continue
            if not SKILL_NAME_RE.fullmatch(name):
                errors.append(f"{path}: invalid directory name")
            try:
                data = path.read_text(encoding="utf-8")
            except UnicodeError:
                errors.append(f"{path}: invalid UTF-8")
                continue
            match = FRONTMATTER_RE.match(data)
            if not match:
                errors.append(f"{path}: missing YAML front matter")
                continue
            fields: dict[str, str] = {}
            for line in match.group("header").splitlines():
                if ":" in line and not line.startswith(" "):
                    key, value = line.split(":", 1)
                    fields[key.strip()] = value.strip()
            if fields.get("name") != name:
                errors.append(f"{path}: front matter name must match directory")
            description = fields.get("description", "").strip("'\" ")
            if len(description) < 20 or len(description) > 1024:
                errors.append(f"{path}: description must have 20-1024 characters")
            if len(data[match.end():].strip()) < 40:
                errors.append(f"{path}: missing procedural body")
            if folder == ".claude/skills":
                expected_link = f"../../../.agents/skills/{name}/SKILL.md"
                if expected_link not in data:
                    errors.append(f"{path}: missing canonical skill reference {expected_link}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    errors, checked = check_links(root)
    errors += check_canonical_domains(root)
    errors += check_skill_manifests(root)
    if errors:
        print("\n".join(f"ERROR {error}" for error in errors), file=sys.stderr)
        print(f"KB check failed: {len(errors)} errors, {checked} links checked", file=sys.stderr)
        return 1
    print(f"KB check PASS: {len(guidance_files(root))} documents, {checked} links, "
          f"{len(REQUIRED_SKILLS)} dual-discovery skills, canonical rodada.bar")
    print("Note: this is NOT a spec acceptance, CI implementation gate or deployed-domain check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
