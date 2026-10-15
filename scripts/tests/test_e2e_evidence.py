"""Synthetic contract fixtures only: these tests never execute Rodada clients."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import subprocess
import sys
import json
import unittest

SPEC = importlib.util.spec_from_file_location("e2e_evidence", Path(__file__).parents[1] / "e2e_evidence.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)
SHA = "a" * 40


class EvidenceContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        artifacts = {}
        for kind in ("android-instrumentation", "playwright-trace", "independent-sql"):
            payload = b"SYNTHETIC UNIT TEST; NOT EXECUTION EVIDENCE"
            (self.root / kind).write_bytes(payload)
            artifacts[kind] = {"path": kind, "sha256": hashlib.sha256(payload).hexdigest(), "sanitized": True, "kind": kind}
        self.proof = {
            "schema_version": 1, "sha": SHA, "evidence_kind": "executed",
            "database": {"engine": "postgresql", "disposable": True, "instance_id": "isolated-unit-fixture"},
            "versions": {key: "synthetic" for key in ("android", "browser", "django", "postgresql", "nextjs")},
            "artifacts": artifacts,
            "review": {"sha": SHA, "independent": True, "open_p0_p1": 0, "reference": "synthetic-review"},
            "invariants": {name: {"status": "PASS", "scenario": "E2E-01", "artifact_ref": "independent-sql"} for name in gate.INVARIANTS},
            "scenarios": [{"id": sid, "sha": SHA, "database_instance_id": "isolated-unit-fixture", "status": "PASS", "reason": "synthetic contract example", "dependencies": [], "task_ids": ["F5", "F7"], "command": "not executed", "run_url": "https://example.invalid/synthetic", "branch": "synthetic", "pr": "synthetic", "started_at": "synthetic", "finished_at": "synthetic", "surfaces": sorted(gate.SURFACES), "canonical_ids": {"venue": ["synthetic-venue"], "tab": ["synthetic-tab", "synthetic-tab-2"], "order": ["synthetic-order"], "order_item": ["synthetic-item"], "charge": ["synthetic-charge"], "table": ["synthetic-table"], "occupancy": ["synthetic-occupancy"]}, "artifact_refs": list(artifacts), "sql": {"independent": True, "status": "PASS", "command": "not executed", "artifact_ref": "independent-sql"}} for sid in sorted(gate.SCENARIOS)],
        }

    def test_occupancy_race_needs_real_context_without_fabricating_tab(self):
        race = next(r for r in self.proof["scenarios"] if r["id"] == "E2E-08")
        del race["canonical_ids"]["tab"]
        self.assertEqual([], gate.validate(self.proof, self.root, SHA))
        del race["canonical_ids"]["occupancy"]
        self.assertTrue(gate.validate(self.proof, self.root, SHA))

    def test_missing_runtime_metadata_cannot_authorize_go(self):
        for value in ("NOT_AVAILABLE", "emulator API NOT_AVAILABLE"):
            self.proof["versions"]["android"] = value
            self.assertIn("all runtime versions required", gate.validate(self.proof, self.root, SHA))

    def test_complete_synthetic_contract_shape(self):
        self.assertEqual([], gate.validate(self.proof, self.root, SHA))

    def test_every_non_pass_status_blocks(self):
        for status in ("FAIL", "SKIP", "BLOCKED", "PENDING", "PAID"):
            with self.subTest(status=status):
                self.proof["scenarios"][0]["status"] = status
                self.assertTrue(gate.validate(self.proof, self.root, SHA))

    def test_each_critical_invariant_blocks(self):
        for name in gate.INVARIANTS:
            proof = copy.deepcopy(self.proof)
            proof["invariants"][name]["status"] = "FAIL"
            with self.subTest(invariant=name):
                self.assertTrue(gate.validate(proof, self.root, SHA))

    def test_missing_duplicate_sha_database_and_native_proofs(self):
        mutations = [lambda d: d["scenarios"].pop(), lambda d: d["scenarios"].append(d["scenarios"][0]), lambda d: d["scenarios"][0].update(sha="b" * 40), lambda d: d["scenarios"][0].update(database_instance_id="another-db"), lambda d: d["artifacts"].pop("android-instrumentation"), lambda d: d.update(evidence_kind="synthetic"), lambda d: d["database"].update(engine="sqlite"), lambda d: d["review"].update(independent=False), lambda d: d["scenarios"][0]["sql"].update(status="PENDING")]
        for mutation in mutations:
            proof = copy.deepcopy(self.proof)
            mutation(proof)
            self.assertTrue(gate.validate(proof, self.root, SHA))

    def test_cli_malformed_json_is_no_go(self):
        manifest = self.root / "manifest.json"
        manifest.write_text("{")
        result = subprocess.run([sys.executable, str(SPEC.origin), str(manifest), "--sha", SHA], capture_output=True, text=True, check=False)
        self.assertEqual(1, result.returncode)
        report = json.loads(result.stdout)
        self.assertEqual("NO-GO", report["automated_gate"])
        self.assertEqual({"NOT_VERIFIED"}, set(report["physical_signoff"].values()))
        self.assertEqual("", result.stderr)

    def test_native_claim_cannot_reference_only_sql(self):
        self.proof["scenarios"][0]["artifact_refs"] = ["independent-sql"]
        self.assertTrue(gate.validate(self.proof, self.root, SHA))

    def test_invariant_must_reference_own_scenario_sql(self):
        self.proof["artifacts"]["misc"] = dict(self.proof["artifacts"]["independent-sql"], kind="misc")
        self.proof["invariants"]["ledger_reconciled"]["artifact_ref"] = "misc"
        self.assertTrue(gate.validate(self.proof, self.root, SHA))
        self.proof["artifacts"]["other-sql"] = dict(self.proof["artifacts"]["independent-sql"])
        self.proof["invariants"]["ledger_reconciled"]["artifact_ref"] = "other-sql"
        self.assertTrue(gate.validate(self.proof, self.root, SHA))

    def test_all_canonical_id_fields_are_typed(self):
        for key, value in (("order", None), ("payment", 123), ("charge", []), ("payment", [123])):
            proof = copy.deepcopy(self.proof)
            proof["scenarios"][0]["canonical_ids"][key] = value
            with self.subTest(key=key, value=value):
                self.assertTrue(gate.validate(proof, self.root, SHA))

    def test_financial_and_order_invariants_need_relevant_ids(self):
        for key in ("order", "order_item", "charge"):
            proof = copy.deepcopy(self.proof)
            del proof["scenarios"][0]["canonical_ids"][key]
            self.assertTrue(gate.validate(proof, self.root, SHA))
        self.proof["scenarios"][0]["canonical_ids"]["tab"] = ["same", "same"]
        self.assertTrue(gate.validate(self.proof, self.root, SHA))

    def test_self_symlink_returns_json_no_go(self):
        loop = self.root / "loop"
        loop.symlink_to("loop")
        self.proof["artifacts"]["independent-sql"]["path"] = "loop"
        self.assertTrue(gate.validate(self.proof, self.root, SHA))
        manifest = self.root / "manifest.json"
        manifest.write_text(json.dumps(self.proof))
        result = subprocess.run([sys.executable, str(SPEC.origin), str(manifest), "--sha", SHA], capture_output=True, text=True, check=False)
        self.assertEqual(1, result.returncode)
        self.assertEqual("NO-GO", json.loads(result.stdout)["automated_gate"])
        self.assertEqual("", result.stderr)
        self.assertNotIn(str(self.root), result.stdout)

    def test_error_reports_do_not_expose_local_paths(self):
        self.proof["artifacts"]["independent-sql"]["path"] = "missing-file"
        self.assertNotIn(str(self.root), json.dumps(gate.validate(self.proof, self.root, SHA)))
        self.proof["artifacts"][str(self.root)] = {"path": "missing-file"}
        self.proof["scenarios"][0]["id"] = str(self.root)
        self.assertNotIn(str(self.root), json.dumps(gate.validate(self.proof, self.root, SHA)))
        result = subprocess.run([sys.executable, str(SPEC.origin), str(self.root / "absent.json"), "--sha", SHA], capture_output=True, text=True, check=False)
        self.assertEqual(1, result.returncode)
        self.assertEqual("NO-GO", json.loads(result.stdout)["automated_gate"])
        self.assertNotIn(str(self.root), result.stdout)
        self.assertEqual("", result.stderr)

    def test_digest_and_traversal(self):
        (self.root / "independent-sql").write_text("tampered")
        self.assertTrue(gate.validate(self.proof, self.root, SHA))
        self.proof["artifacts"]["android-instrumentation"]["path"] = "../outside"
        self.assertTrue(gate.validate(self.proof, self.root, SHA))

    def test_malformed_records_fail_closed(self):
        for field in ("scenarios", "artifacts", "database", "versions", "review", "invariants"):
            proof = copy.deepcopy(self.proof)
            proof[field] = None
            self.assertTrue(gate.validate(proof, self.root, SHA))
        self.proof["scenarios"][0]["sql"]["artifact_ref"] = []
        self.assertTrue(gate.validate(self.proof, self.root, SHA))


if __name__ == "__main__":
    unittest.main()
