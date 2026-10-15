#!/usr/bin/env python3
"""Offline, fail-closed #106 evidence contract; never executes supplied commands."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

SCENARIOS = {f"E2E-{number:02d}" for number in range(1, 15)}
SURFACES = {"android-instrumented", "attendance-web", "guest", "bar", "kitchen", "manage", "cash", "django"}
INVARIANTS = {"ledger_reconciled", "no_duplicates", "no_false_paid", "venue_isolated", "no_lost_orders", "guest_revoked", "order_on_tab", "new_not_preparing", "offline_no_false_confirmation", "separate_tab_ledgers"}
PHYSICAL = ["physical Android and bar Wi-Fi", "Tap/NFC/Pix providers", "printers", "fiscal acceptance", "VR System rollback rehearsal"]


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate(document, root, expected_sha):
    """Return all actionable errors; only local sanitized artifact paths are read."""
    errors = []
    if not isinstance(document, dict):
        return ["manifest must be an object"]
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        errors.append("expected SHA must be full lowercase 40-hex")
    if document.get("schema_version") != 1 or document.get("sha") != expected_sha:
        errors.append("schema version or exact SHA mismatch")
    if document.get("evidence_kind") != "executed":
        errors.append("mock, synthetic or planned evidence cannot authorize GO")
    database = document.get("database", {})
    if not isinstance(database, dict):
        database = {}
    if database.get("engine") != "postgresql" or database.get("disposable") is not True or not nonempty(database.get("instance_id")):
        errors.append("shared disposable PostgreSQL instance required")
    versions = document.get("versions", {})
    if not isinstance(versions, dict) or any(not nonempty(versions.get(key)) for key in ("android", "browser", "django", "postgresql", "nextjs")):
        errors.append("all runtime versions required")
    artifacts = document.get("artifacts", {})
    if not isinstance(artifacts, dict):
        artifacts = {}
    valid_artifacts = set()
    kinds = set()
    for key, entry in artifacts.items():
        try:
            if not isinstance(entry, dict) or entry.get("sanitized") is not True:
                raise ValueError("sanitized artifact record required")
            relative = Path(entry["path"])
            path = (root / relative).resolve()
            if relative.is_absolute() or not path.is_relative_to(root.resolve()):
                raise ValueError("artifact escapes evidence root")
            data = path.read_bytes()
            if not data or hashlib.sha256(data).hexdigest() != entry.get("sha256"):
                raise ValueError("empty artifact or digest mismatch")
            if not nonempty(entry.get("kind")):
                raise ValueError("artifact kind required")
            valid_artifacts.add(key)
            kinds.add(entry["kind"])
        except (KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
            reference = key if isinstance(key, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", key) else "INVALID_REFERENCE"
            errors.append(f"artifact {reference}: invalid or unreadable evidence ({type(exc).__name__})")
    if not {"android-instrumentation", "playwright-trace", "independent-sql"}.issubset(kinds):
        errors.append("native instrumentation, Playwright trace and independent SQL artifacts required")
    records = document.get("scenarios", [])
    if not isinstance(records, list):
        records = []
        errors.append("scenarios must be a list")
    seen = set()
    observed_surfaces = set()
    records_by_id = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"scenario {index}: must be an object")
            continue
        sid = record.get("id")
        label = sid if isinstance(sid, str) and sid in SCENARIOS else str(index)
        if not isinstance(sid, str) or sid not in SCENARIOS or sid in seen:
            errors.append(f"{label}: unknown or duplicate scenario")
        if isinstance(sid, str):
            seen.add(sid)
            records_by_id[sid] = record
        if not isinstance(record.get("status"), str) or record.get("status") not in {"PASS", "FAIL", "SKIP", "BLOCKED"}:
            errors.append(f"{label}: invalid status")
        if record.get("status") != "PASS" or not nonempty(record.get("reason")):
            errors.append(f"{label}: PASS with explicit reason required")
        if record.get("sha") != expected_sha or record.get("database_instance_id") != database.get("instance_id"):
            errors.append(f"{label}: SHA/shared database mismatch")
        for key in ("command", "run_url", "branch", "pr", "started_at", "finished_at"):
            if not nonempty(record.get(key)):
                errors.append(f"{label}: {key} required")
        task_ids = record.get("task_ids")
        if not isinstance(task_ids, list) or not task_ids or any(not isinstance(task, str) or not re.fullmatch(r"(?:A[1-6]|[B-E][1-7]|F[1-8])", task) for task in task_ids):
            errors.append(f"{label}: valid A1–F8 task IDs required")
        dependencies = record.get("dependencies")
        if not isinstance(dependencies, list) or any(not isinstance(dep, str) or dep not in SCENARIOS or dep == sid for dep in dependencies):
            errors.append(f"{label}: valid dependencies required")
        surfaces = record.get("surfaces")
        if not isinstance(surfaces, list) or not surfaces or any(not isinstance(surface, str) or surface not in SURFACES for surface in surfaces):
            errors.append(f"{label}: real surfaces required")
        else:
            observed_surfaces.update(surfaces)
        ids = record.get("canonical_ids")
        if not isinstance(ids, dict) or any(not isinstance(ids.get(key), list) or not ids[key] or any(not nonempty(value) for value in ids[key]) for key in ("venue", "tab")):
            errors.append(f"{label}: canonical Venue/Tab IDs required")
        if isinstance(ids, dict) and any(not nonempty(key) or not isinstance(values, list) or not values or any(not nonempty(value) for value in values) for key, values in ids.items()):
            errors.append(f"{label}: every supplied canonical ID field must be a nonempty string list")
        refs = record.get("artifact_refs")
        if not isinstance(refs, list) or not refs or any(not isinstance(ref, str) or ref not in valid_artifacts for ref in refs):
            errors.append(f"{label}: verified artifact references required")
        if isinstance(refs, list) and isinstance(surfaces, list):
            linked_kinds = {artifacts[ref]["kind"] for ref in refs if isinstance(ref, str) and ref in valid_artifacts}
            if "android-instrumented" in surfaces and "android-instrumentation" not in linked_kinds:
                errors.append(f"{label}: native surface lacks linked instrumentation artifact")
            if any(surface in surfaces for surface in SURFACES - {"android-instrumented", "django"}) and "playwright-trace" not in linked_kinds:
                errors.append(f"{label}: browser surface lacks linked Playwright trace")
        sql = record.get("sql")
        if not isinstance(sql, dict) or sql.get("independent") is not True or sql.get("status") != "PASS" or not nonempty(sql.get("command")) or not isinstance(sql.get("artifact_ref"), str) or sql.get("artifact_ref") not in valid_artifacts or artifacts[sql["artifact_ref"]].get("kind") != "independent-sql":
            errors.append(f"{label}: independent passing SQL readback required")
        elif not isinstance(refs, list) or sql["artifact_ref"] not in refs:
            errors.append(f"{label}: SQL artifact must belong to scenario artifact_refs")
    if seen != SCENARIOS:
        errors.append("all E2E-01..14 required exactly once")
    if observed_surfaces != SURFACES:
        errors.append("all real client surfaces required across suite")
    invariants = document.get("invariants", {})
    if not isinstance(invariants, dict):
        invariants = {}
    for name in sorted(INVARIANTS):
        proof = invariants.get(name)
        if not isinstance(proof, dict) or proof.get("status") != "PASS" or not isinstance(proof.get("scenario"), str) or proof.get("scenario") not in seen or not isinstance(proof.get("artifact_ref"), str) or proof.get("artifact_ref") not in valid_artifacts:
            errors.append(f"invariant {name}: passing linked proof required")
            continue
        scenario = records_by_id[proof["scenario"]]
        sql = scenario.get("sql")
        refs = scenario.get("artifact_refs")
        if not isinstance(sql, dict) or proof["artifact_ref"] != sql.get("artifact_ref") or not isinstance(refs, list) or proof["artifact_ref"] not in refs or artifacts[proof["artifact_ref"]].get("kind") != "independent-sql":
            errors.append(f"invariant {name}: proof must match the claimed scenario's independent SQL artifact")
        required_ids = {
            "ledger_reconciled": ("charge",),
            "no_duplicates": ("order", "charge"),
            "no_lost_orders": ("order",),
            "order_on_tab": ("order",),
            "new_not_preparing": ("order", "order_item"),
            "separate_tab_ledgers": ("charge",),
        }.get(name, ())
        ids = scenario.get("canonical_ids")
        if not isinstance(ids, dict) or any(not isinstance(ids.get(key), list) or not ids[key] for key in required_ids):
            errors.append(f"invariant {name}: relevant canonical IDs required: {required_ids}")
        if name == "separate_tab_ledgers" and (not isinstance(ids, dict) or not isinstance(ids.get("tab"), list) or len({value for value in ids["tab"] if isinstance(value, str)}) < 2):
            errors.append("invariant separate_tab_ledgers: at least two distinct Tab IDs required")
    review = document.get("review", {})
    if not isinstance(review, dict) or review.get("sha") != expected_sha or review.get("independent") is not True or type(review.get("open_p0_p1")) is not int or review.get("open_p0_p1") != 0 or not nonempty(review.get("reference")):
        errors.append("independent review of exact SHA with no open P0/P1 required")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--sha", required=True, help="trusted tested commit SHA")
    parser.add_argument("--root", type=Path, help="artifact root (defaults to manifest parent)")
    args = parser.parse_args()
    try:
        document = json.loads(args.manifest.read_text())
        errors = validate(document, args.root or args.manifest.parent, args.sha)
    except (OSError, RuntimeError, ValueError, TypeError) as exc:
        errors = [f"unreadable or malformed evidence ({type(exc).__name__})"]
    print(json.dumps({"sha": args.sha, "automated_gate": "NO-GO" if errors else "GO", "errors": errors, "physical_signoff": {item: "NOT_VERIFIED" for item in PHYSICAL}, "limitation": "Offline contract/digest verification; trusted producer logs, runtime identity, sanitization and review provenance require independent inspection."}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
