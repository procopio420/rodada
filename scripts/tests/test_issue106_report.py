import importlib.util
import json
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
spec = importlib.util.spec_from_file_location("report", Path(__file__).resolve().parents[1] / "build-issue106-report.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReportBoundaryTests(unittest.TestCase):
    def test_stale_cluster_receipts_cannot_authorize_pass_or_supply_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sha = "a" * 40
            (root / "execution.json").write_text(json.dumps({"sha":sha,"result":"PASS"}))
            (root / "qr-lifecycle-sql.json").write_text(json.dumps({"sha":sha,"database_instance_id":"old-cluster","status":"PASS"}))
            report = module.build(root, sha, {"database_instance_id":"current","venue_id":"venue"}, {}, "local", "branch", "pr")
            self.assertNotIn("qr-lifecycle-sql.json", report["artifacts"])
            self.assertEqual(len(report["scenarios"]), 14)
            self.assertTrue(all(record["status"] == "BLOCKED" for record in report["scenarios"]))
            self.assertTrue(module.validate(report, root, sha))

    def test_capture_sha_mismatch_is_rejected_before_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "execution.json").write_text('{"sha":"wrong"}')
            with self.assertRaisesRegex(ValueError, "SHA mismatch"):
                module.build(root, "a" * 40, {"database_instance_id":"current"}, {}, "local", "branch", "pr")


    def test_final_sql_promotes_only_unchanged_current_receipts(self):
        # Entirely synthetic: checks compiler linkage, never client execution.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); sha = "a" * 40
            fixture = {"venue_id":"synthetic-venue", "database_instance_id":"synthetic-cluster"}
            (root / "execution.json").write_text(json.dumps({"sha":sha,"result":"PASS","started_at":"synthetic","finished_at":"synthetic"}))
            sources = {}
            for name in {n for case in module.CASES.values() for n in case[1]}:
                data = {"sha":sha,"status":"PASS","database_instance_id":"synthetic-cluster","tab_ids":["tab-a","tab-b"],"order_ids":["order-a"],"item_ids":["item-a"],"charge_ids":["charge-a"],"table_ids":["table-a"],"occupancy_ids":["occupancy-a"]}
                path = root / name; path.write_text(json.dumps(data))
                sources[name] = hashlib.sha256(path.read_bytes()).hexdigest()
            final = {"sha":sha,"status":"PASS","database_instance_id":"synthetic-cluster","source_sha256":sources,"invariants":{name:"PASS" for name in module.INVARIANTS}}
            (root / "final-state-sql.json").write_text(json.dumps(final))
            for token in ("context-readback","compose","catalog","offline-conflict","offline-revocation","recovery"):
                (root / f"android-{token}-instrumentation.txt").write_text("SYNTHETIC NOT RUNTIME")
            (root / "sanitized-traces").mkdir()
            for token in ("qr-lifecycle","browser-origins","android-native-to-web","financial","unavailable","concurrency","authorization","sse-recovery","pending-payment"):
                (root / "sanitized-traces" / f"{token}.zip").write_text("SYNTHETIC NOT RUNTIME")
            versions = {key:"synthetic" for key in ("android","browser","django","postgresql","nextjs")}
            review = {"sha":sha,"independent":True,"open_p0_p1":0,"reference":"synthetic-only"}
            report = module.build(root,sha,fixture,versions,"synthetic","synthetic","synthetic",review)
            self.assertEqual([], module.validate(report,root,sha))
            # Rewriting a current-SHA receipt still invalidates final reconciliation.
            path = root / next(iter(sources)); path.write_text(path.read_text()+" ")
            report = module.build(root,sha,fixture,versions,"synthetic","synthetic","synthetic",review)
            self.assertNotIn("final-state-sql.json", report["artifacts"])
            self.assertTrue(all(p["status"] == "BLOCKED" for p in report["invariants"].values()))
            self.assertTrue(module.validate(report,root,sha))
