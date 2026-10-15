import importlib.util
import json
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
