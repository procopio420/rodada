"""Validate completeness/integrity of operator evidence, never certify hardware."""

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SCENARIOS = (
    "pairing", "station_routing", "accents_width_cut", "connection_loss",
    "computer_restart", "printer_disconnect", "duplicate_job", "two_agents",
    "printer_replacement", "revocation", "spooler_failure", "operator_recovery",
    "upgrade_rollback",
)


def evaluate(record: dict[str, Any], root: Path) -> list[str]:
    gaps = []
    if record.get("schema_version") != 1:
        gaps.append("schema_version")
    if not re.fullmatch(r"[0-9a-f]{40}", str(record.get("commit", ""))):
        gaps.append("commit")
    for field in ("operator", "windows_build", "printer_model", "driver_version", "connection", "profile_id"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            gaps.append(field)
    if record.get("mode") != "PHYSICAL":
        gaps.append("physical_execution")
    if record.get("owner_rollout_authorized") is not True:
        gaps.append("owner_rollout_authorized")
    for gate in ("authenticode", "antivirus_smartscreen", "signed_installer_sha256"):
        if record.get("release_gates", {}).get(gate, {}).get("status") != "PASS":
            gaps.append("release:" + gate)
    rows = record.get("scenarios", {})
    gates = record.get("release_gates", {})
    for name in (*SCENARIOS, *gates):
        row = rows.get(name) if name in SCENARIOS else gates.get(name)
        if not isinstance(row, dict) or row.get("status") != "PASS":
            gaps.append("scenario:" + name)
            continue
        evidence = row.get("evidence", [])
        if not isinstance(evidence, list) or not evidence:
            gaps.append("evidence:" + name)
            continue
        for item in evidence:
            try:
                relative = Path(item["path"])
                path = root / relative
                if relative.is_absolute() or ".." in relative.parts or path.is_symlink():
                    raise ValueError("Unsafe evidence path")
                if not path.resolve().is_relative_to(root.resolve()):
                    raise ValueError("Evidence outside record")
                if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
                    raise ValueError("Digest mismatch")
            except (OSError, KeyError, TypeError, ValueError):
                gaps.append("integrity:" + name)
    return sorted(set(gaps))


def main() -> None:
    path = Path(sys.argv[1])
    gaps = evaluate(json.loads(path.read_text()), path.parent)
    print(json.dumps({"decision": "NO_GO" if gaps else "READY_FOR_SIGNOFF", "gaps": gaps}))
    # Completeness never grants production GO or authenticates operator assertions.
    raise SystemExit(1 if gaps else 0)


if __name__ == "__main__":
    main()
