#!/usr/bin/env python3
"""Summarize executed receipts into the #186 contract; missing coverage stays NO-GO.

Reads only a runner-created capture directory. It never executes manifest commands,
never imports older receipts, and never invents an independent review or PSP proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone
from e2e_evidence import validate, INVARIANTS

# Partial contracts remain BLOCKED even when their implemented subcases passed.
CASES = {
    "E2E-01": ("A2 A5 A6", ["qr-lifecycle-sql.json"], ["guest", "attendance-web"], ""),
    "E2E-02": ("A3 A6", ["browser-origins-sql.json", "android-compose-web-sql.json"], ["guest", "attendance-web", "android-instrumented"], "Native readback of the two contextual Tabs remains unproven."),
    "E2E-03": ("B2 B3 B7", ["browser-origins-sql.json", "android-compose-web-sql.json"], ["guest", "attendance-web", "android-instrumented"], ""),
    "E2E-04": ("B4 B5 B7", ["browser-origins-sql.json", "android-compose-web-sql.json"], ["bar", "kitchen"], "Native/management projection after READY remains incomplete."),
    "E2E-05": ("B6 B7", [], ["guest", "attendance-web", "android-instrumented"], "Catalog rupture after cart is not yet executed across all three origins."),
    "E2E-06": ("C3 C7", ["financial-sql.json"], ["cash", "attendance-web"], ""),
    "E2E-07": ("C5 C7", ["financial-sql.json"], ["cash", "manage"], "Negative cashier/manager capability and business cutoff cases remain incomplete."),
    "E2E-08": ("D2 D3 D7", ["concurrency-sql.json"], ["django", "attendance-web"], ""),
    "E2E-09": ("D4 D7", ["browser-origins-sql.json", "android-web-cross-surface.json"], ["guest", "android-instrumented"], "Native UI double-tap and divergent-body negative remain unproven."),
    "E2E-10": ("D5 D6 D7", ["revocation-sql.json", "isolation-sql.json"], ["attendance-web", "android-instrumented", "guest"], "Native revocation/replay, expiry/refresh and Guest/Host A/B crossings remain incomplete."),
    "E2E-11": ("E2 E3 E7", ["android-web-cross-surface.json"], ["android-instrumented", "bar"], ""),
    "E2E-12": ("E4 E5 E7", ["sse-sql.json", "browser-origins-sql.json"], ["attendance-web", "kitchen"], ""),
    "E2E-13": ("A4 A5 A6", ["qr-lifecycle-sql.json"], ["guest", "attendance-web"], ""),
    "E2E-14": ("C4 C6 C7", ["pending-payment-sql.json", "financial-sql.json"], ["cash", "attendance-web"], ""),
}


def build(root, sha, fixture, versions, run_url, branch, pr, review=None):
    execution = json.loads((root / "execution.json").read_text())
    if execution.get("sha") != sha:
        raise ValueError("execution SHA mismatch")
    instance = fixture["database_instance_id"]
    artifacts, receipts = {}, {}
    for path in sorted(root.glob("*.json")):
        if path.name in {"execution.json", "manifest.json", "gate.json"}:
            continue
        try:
            data = json.loads(path.read_text())
        except ValueError:
            continue
        if data.get("sha") != sha or data.get("database_instance_id") != instance:
            continue
        if data.get("status", data.get("result")) != "PASS":
            continue
        kind = "independent-sql" if path.name.endswith("-sql.json") or path.name == "android-web-cross-surface.json" else "receipt"
        artifacts[path.name] = {"path":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"kind":kind,"sanitized":True}
        receipts[path.name] = data
    for path in sorted(root.rglob("*")):
        if path.is_file() and (path.name.endswith("-instrumentation.txt") or (path.suffix == ".zip" and path.parent.name == "sanitized-traces")):
            key = str(path.relative_to(root))
            artifacts[key] = {"path":key,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"kind":"playwright-trace" if path.suffix == ".zip" else "android-instrumentation","sanitized":True}
    records = []
    for sid, (tasks, required, surfaces, gap) in CASES.items():
        missing = [name for name in required if name not in receipts]
        reason = gap or ("Missing current-SHA shared-cluster receipts: " + ", ".join(missing) if missing else "Real client execution and independent PostgreSQL reconciliation completed.")
        status = "BLOCKED" if gap or missing or not required else "PASS"
        if execution.get("result") == "FAIL" and missing:
            status = "FAIL"; reason = "Runner failed at " + execution.get("last_step", "unknown") + "; " + reason
        refs = [name for name in required if name in receipts]
        trace_tests = {
            "E2E-01": ["qr-lifecycle"], "E2E-02": ["browser-origins", "android-native-to-web"],
            "E2E-03": ["browser-origins", "android-native-to-web"], "E2E-04": ["browser-origins", "android-native-to-web"],
            "E2E-05": ["unavailable"], "E2E-06": ["financial"], "E2E-07": ["financial"],
            "E2E-08": ["concurrency"], "E2E-09": ["browser-origins", "android-native-to-web"],
            "E2E-10": ["authorization"], "E2E-11": ["android-native-to-web"],
            "E2E-12": ["sse-recovery", "browser-origins"], "E2E-13": ["qr-lifecycle"], "E2E-14": ["pending-payment", "financial"],
        }
        refs += [name for name, a in artifacts.items() if a["kind"] == "playwright-trace" and any(test in name for test in trace_tests[sid])]
        if "android-instrumented" in surfaces:
            refs += [name for name, a in artifacts.items() if a["kind"] == "android-instrumentation" and ("compose" in name if sid in {"E2E-02", "E2E-03", "E2E-04"} else "recovery" in name)]
        ids = {"venue":[fixture["venue_id"]]}
        mapping = {"tab_ids":"tab", "tab_id":"tab", "original_tab_id":"tab", "order_ids":"order", "original_order_id":"order", "original_order_item_ids":"order_item", "charge_ids":"charge", "payment_ids":"payment", "occupancy_ids":"occupancy", "occupancy_id":"occupancy"}
        for name in required:
            for source, target in mapping.items():
                value = receipts.get(name, {}).get(source)
                if value:
                    ids.setdefault(target, []).extend(value if isinstance(value, list) else [value])
        ids = {k:sorted(set(v)) for k,v in ids.items()}
        sql_ref = next((name for name in required if name in artifacts and artifacts[name]["kind"] == "independent-sql"), None)
        records.append({"id":sid,"status":status,"reason":reason,"sha":sha,"database_instance_id":instance,"task_ids":tasks.split(),"dependencies":[],"surfaces":surfaces,"canonical_ids":ids,"artifact_refs":refs,"command":"bash scripts/run-issue106-shared.sh","run_url":run_url,"branch":branch,"pr":pr,"started_at":execution.get("started_at","NOT_RECORDED"),"finished_at":execution.get("finished_at","NOT_RECORDED"),"sql":{"independent":bool(sql_ref),"status":"PASS" if sql_ref else "BLOCKED","command":"runner independent PostgreSQL verifiers","artifact_ref":sql_ref}})
    return {"schema_version":1,"sha":sha,"evidence_kind":"executed","database":{"engine":"postgresql","disposable":True,"instance_id":instance},"versions":versions,"artifacts":artifacts,"scenarios":records,"invariants":{name:{"status":"BLOCKED","reason":"Requires explicit reviewed scenario mapping; no automatic promotion."} for name in sorted(INVARIANTS)},"review":review or {"sha":sha,"independent":False,"open_p0_p1":None,"reference":"NOT_VERIFIED"}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path);p.add_argument("--fixture",required=True,type=Path);p.add_argument("--versions",required=True,type=Path)
    p.add_argument("--sha",required=True);p.add_argument("--run-url",required=True);p.add_argument("--pr",required=True);p.add_argument("--review",type=Path)
    a=p.parse_args()
    document=build(a.root,a.sha,json.loads(a.fixture.read_text()),json.loads(a.versions.read_text()),a.run_url,subprocess.check_output(["git","branch","--show-current"],text=True).strip(),a.pr,json.loads(a.review.read_text()) if a.review else None)
    (a.root/"manifest.json").write_text(json.dumps(document,indent=2)+"\n")
    errors=validate(document,a.root,a.sha)
    counts={status:sum(r["status"]==status for r in document["scenarios"]) for status in ("PASS","FAIL","SKIP","BLOCKED")}
    gate={"sha":a.sha,"generated_at":datetime.now(timezone.utc).isoformat(),"counts":counts,"automated_gate":"NO-GO" if errors else "GO","errors":errors,"physical_gates":"NOT_VERIFIED; separate onsite acceptance"}
    (a.root/"gate.json").write_text(json.dumps(gate,indent=2)+"\n")
    print(json.dumps({k:gate[k] for k in ("sha","counts","automated_gate")}))
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
