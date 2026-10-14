#!/usr/bin/env python3
"""Validate a conservative spec acceptance-evidence registry and print coverage.

Evidence is only a pointer: this tool cannot query GitHub, prove CI outcome,
validate real deployments, or approve acceptance automatically.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/agents/evidence/registry.json"
ACCEPTANCE_ID = re.compile(r"\bTS\d{3}-\d{2}\b")
SHA = re.compile(r"^[0-9a-f]{40}$")
LEVELS = ("UNVERIFIED", "TESTED", "CI_VERIFIED", "HOMOLOGATED", "DEPLOYED")


def source_path(root: Path, raw: str) -> Path | None:
    if not isinstance(raw, str) or not raw or raw.startswith("/"):
        return None
    resolved = (root / raw).resolve()
    return resolved if resolved.is_relative_to(root.resolve()) else None


def gh_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and parsed.hostname == "github.com" and bool(parsed.path.strip("/"))


def load_registry(path: Path = REGISTRY) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise ValueError("registry must have entries array")
    return data["entries"]


def validate(root: Path = ROOT, path: Path = REGISTRY) -> list[str]:
    errors: list[str] = []
    try:
        entries = load_registry(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [f"invalid registry: {exc}"]
    seen = set()
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"row {i}: not an object")
            continue
        key, spec = entry.get("criterion_key"), entry.get("spec_path")
        prefix = f"row {i} ({key}):"
        sp = source_path(root, spec)
        if (not isinstance(spec, str) or not re.fullmatch(r"specs/[^/]+", spec)
                or sp is None or not (sp / "acceptance.md").is_file()):
            errors.append(f"{prefix} invalid spec_path (use full specs/<directory>)")
            continue
        if not isinstance(key, str) or not re.fullmatch("[a-z0-9][a-z0-9-]{2,75}", key):
            errors.append(f"{prefix} invalid criterion_key")
        identity = (spec, key)
        if identity in seen:
            errors.append(f"{prefix} duplicate identity")
        seen.add(identity)
        selector = entry.get("criterion_selector")
        contract = (sp / "acceptance.md").read_text(encoding="utf-8")
        if not isinstance(selector, dict) or selector.get("type") not in ("id", "contains"):
            errors.append(f"{prefix} invalid criterion selector")
        elif not isinstance(selector.get("value"), str) or not selector["value"].strip():
            errors.append(f"{prefix} empty selector value")
        elif selector["type"] == "id" and selector["value"] not in set(ACCEPTANCE_ID.findall(contract)):
            errors.append(f"{prefix} acceptance ID does not exist in {spec}")
        elif selector["type"] == "contains" and selector["value"] not in contract:
            errors.append(f"{prefix} acceptance excerpt is absent from {spec}")
        paths = entry.get("planned_tests")
        if not isinstance(paths, list) or not paths or not all(isinstance(x, str) for x in paths):
            errors.append(f"{prefix} planned_tests must be nonempty paths")
        else:
            for test_path in paths:
                tp = source_path(root, test_path)
                if tp is None or not tp.is_file() or not (
                    test_path.startswith(("apps/api/tests/", "apps/web/tests/",
                                          "apps/attendance-android/", "scripts/"))
                ):
                    errors.append(f"{prefix} missing/invalid test source: {test_path}")
        status = entry.get("status")
        if status not in LEVELS:
            errors.append(f"{prefix} invalid status {status}")
            continue
        proofs = entry.get("proofs", {})
        if not isinstance(proofs, dict):
            errors.append(f"{prefix} proofs must be an object")
            continue
        if status == "UNVERIFIED" and any(proofs.values()):
            errors.append(f"{prefix} UNVERIFIED cannot contain claimed proof")
        if status in LEVELS[1:]:
            executed = proofs.get("test")
            if not isinstance(executed, dict) or not (
                SHA.fullmatch(str(executed.get("commit_sha", "")))
                and gh_url(executed.get("run_url"))
                and isinstance(executed.get("command"), str)
                and len(executed["command"]) > 5
                and executed.get("result") == "PASS"
                and executed.get("environment") in ("isolated_ci", "isolated_local", "pilot")
            ):
                errors.append(f"{prefix} TESTED needs actual PASS command, SHA, environment and GitHub evidence URL")
        if status in LEVELS[2:]:
            ci = proofs.get("ci")
            executed = proofs.get("test", {})
            if not isinstance(ci, dict) or not (
                ci.get("conclusion") == "success" and gh_url(ci.get("run_url"))
                and SHA.fullmatch(str(ci.get("commit_sha", "")))
                and isinstance(executed, dict)
                and ci.get("commit_sha") == executed.get("commit_sha")
            ):
                errors.append(f"{prefix} CI_VERIFIED needs successful CI URL on identical commit SHA")
        if status in LEVELS[3:]:
            signoff = proofs.get("signoff")
            if not isinstance(signoff, dict) or not (
                signoff.get("decision") == "APPROVED"
                and isinstance(signoff.get("reviewer"), str) and signoff["reviewer"].strip()
                and isinstance(signoff.get("observed_at"), str)
                and isinstance(signoff.get("notes"), str) and signoff["notes"].strip()
            ):
                errors.append(f"{prefix} HOMOLOGATED needs explicit human acceptance and observed evidence")
        if status == "DEPLOYED":
            dep = proofs.get("deployment")
            if not isinstance(dep, dict) or not (
                dep.get("commit_sha") == proofs.get("test", {}).get("commit_sha")
                and isinstance(dep.get("deployment_id"), str) and dep["deployment_id"]
                and isinstance(dep.get("environment"), str) and dep["environment"]
                and isinstance(dep.get("url"), str) and urlparse(dep["url"]).scheme == "https"
            ):
                errors.append(f"{prefix} DEPLOYED needs same SHA and actual deployment ID/URL/environment")
    return errors


def inventory(root: Path = ROOT, registry: list[dict] | None = None) -> list[dict]:
    registry = registry if registry is not None else load_registry()
    rows = []
    for spec in sorted((root / "specs").glob("*/acceptance.md")):
        rel = spec.parent.relative_to(root).as_posix()
        ids = set(ACCEPTANCE_ID.findall(spec.read_text(encoding="utf-8")))
        matching = [e for e in registry if e["spec_path"] == rel]
        mapped = {e["criterion_selector"]["value"] for e in matching if e["criterion_selector"]["type"] == "id"}
        rows.append({
            "spec_path": rel,
            "structured_ids": len(ids),
            "mapped_ids": len(mapped & ids),
            "unmapped_ids": len(ids - mapped),
            "registered_rows": len(matching),
            "verified_ci_rows": sum(e["status"] in LEVELS[2:] for e in matching),
            "homologated_rows": sum(e["status"] in LEVELS[3:] for e in matching),
            "status": "UNSTRUCTURED" if not ids else "PARTIAL_REGISTRY" if ids-mapped else "IDS_MAPPED_NOT_ACCEPTED",
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("validate", "report"))
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = parser.parse_args()
    errors = validate()
    if errors:
        for err in errors:
            print("ERROR " + err, file=sys.stderr)
        return 1
    rows = inventory()
    if args.action == "validate":
        print(f"Evidence registry structurally valid: {len(load_registry())} entries, "
              f"{len(rows)} spec paths; no CI/acceptance verified remotely")
    elif args.format == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print("### Rodada spec evidence inventory (structural only)\n")
        print("| Spec path | IDs detected | IDs mapped | Unmapped | Evidence entries | CI-linked | Homologated |")
        print("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
        for row in rows:
            print(f"| `{row['spec_path']}` | {row['structured_ids']} | "
                  f"{row['mapped_ids']} | {row['unmapped_ids']} | "
                  f"{row['registered_rows']} | {row['verified_ci_rows']} | {row['homologated_rows']} |")
        print("\n**Only structural references checked. No tests, Codex evals, "
              "deployment or human acceptance were executed by this report.**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
