"""Evidence schema/coverage tests; dummy CI proofs do NOT assert real CI passes."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "spec_evidence.py"
spec = importlib.util.spec_from_file_location("spec_evidence", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SpecEvidenceTests(unittest.TestCase):
    def test_initial_registry_only_claims_unverified(self):
        self.assertEqual(module.validate(), [])
        entries = module.load_registry()
        self.assertGreaterEqual(len(entries), 7)
        self.assertEqual({e["status"] for e in entries}, {"UNVERIFIED"})

    def test_structured_ids_inventory_does_not_infer_acceptance(self):
        rows = module.inventory()
        self.assertGreaterEqual(len(rows), 30)
        by_name = {r["spec_path"]: r for r in rows}
        self.assertIn("specs/027-table-service-claim", by_name)
        self.assertGreater(by_name["specs/027-table-service-claim"]["structured_ids"], 30)
        self.assertEqual(by_name["specs/027-table-service-claim"]["verified_ci_rows"], 0)
        self.assertIn("specs/025-tenant-host-routing", by_name)

    def fixture(self, root):
        target = root / "specs/001-fixture"
        target.mkdir(parents=True)
        (target / "acceptance.md").write_text("- [ ] TS001-01 — a requirement\n")
        path = root / "apps/api/tests/test_example.py"
        path.parent.mkdir(parents=True)
        path.write_text("# test placeholder")
        entry = {
            "spec_path": "specs/001-fixture",
            "criterion_key": "ts001-01",
            "criterion_selector": {"type": "id", "value": "TS001-01"},
            "planned_tests": ["apps/api/tests/test_example.py"],
            "status": "UNVERIFIED",
            "proofs": {},
        }
        return entry

    def test_unsafe_pass_is_rejected(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = self.fixture(root)
            entry["status"] = "CI_VERIFIED"
            p = root / "registry.json"
            p.write_text(json.dumps({"entries": [entry]}))
            errors = module.validate(root, p)
            self.assertTrue(any("TESTED needs" in e for e in errors))
            self.assertTrue(any("CI_VERIFIED needs" in e for e in errors))

    def test_fake_signed_off_without_signoff_is_rejected(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = self.fixture(root)
            sha = "a" * 40
            entry["status"] = "HOMOLOGATED"
            entry["proofs"] = {
                "test": {"commit_sha": sha, "run_url": "https://github.com/example/repo/actions/runs/1",
                         "command": "python -m pytest apps/api/tests/test_example.py",
                         "result": "PASS", "environment": "isolated_ci"},
                "ci": {"commit_sha": sha, "run_url": "https://github.com/example/repo/actions/runs/1",
                       "conclusion": "success"},
            }
            p = root / "registry.json"
            p.write_text(json.dumps({"entries": [entry]}))
            errors = module.validate(root, p)
            self.assertTrue(any("HOMOLOGATED needs" in e for e in errors))

    def test_missing_selector_and_foreign_path_fail(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = self.fixture(root)
            entry["criterion_selector"]["value"] = "TS999-90"
            entry["planned_tests"] = ["../../tmp/something.py"]
            p = root / "registry.json"
            p.write_text(json.dumps({"entries": [entry]}))
            errors = module.validate(root, p)
            self.assertTrue(any("ID does not exist" in e for e in errors))
            self.assertTrue(any("missing/invalid test" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
