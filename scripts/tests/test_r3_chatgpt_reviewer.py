"""Fail-closed unit coverage for ChatGPT R3 runner; no network, no model calls."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("r3_chatgpt_reviewer", SCRIPTS / "r3_chatgpt_reviewer.py")
reviewer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reviewer)
SHA = "a" * 40
REPO = "procopio420/rodada"
BOT = "rodada-r3-reviewer[bot]"


class ChatGPTReviewerTests(unittest.TestCase):
    def sample(self):
        return {
            "decision": "PASS", "summary": "All changed paths reviewed; no critical findings",
            "files_reviewed": ["apps/api/payments.py"],
            "findings": [],
            "risks_checked": ["idempotency", "tenant separation", "payment replay"],
        }

    def test_complete_qualified_review_passes(self):
        self.assertTrue(reviewer.validate_decision(self.sample(), ["apps/api/payments.py"]))

    def test_missing_file_blocks(self):
        review = self.sample()
        self.assertRaises(reviewer.ReviewBlocked, reviewer.validate_decision, review,
                          ["apps/api/payments.py", "apps/api/ledger.py"])

    def test_forged_or_duplicate_path_blocks(self):
        for bad in (["apps/api/payments.py", "apps/api/payments.py"],
                    ["apps/api/other.py"]):
            review = self.sample()
            review["files_reviewed"] = bad
            with self.subTest(bad=bad), self.assertRaises(reviewer.ReviewBlocked):
                reviewer.validate_decision(review, ["apps/api/payments.py"])

    def test_p0_or_p1_always_blocks(self):
        for severity in ("P0", "P1"):
            review = self.sample()
            review["findings"] = [{"severity": severity, "path": "apps/api/payments.py",
                                   "line": 5, "description": "Payment replay bypass"}]
            with self.subTest(severity=severity):
                self.assertFalse(reviewer.validate_decision(review, ["apps/api/payments.py"]))

    def test_p2_can_be_reported_without_disabling_pass(self):
        review = self.sample()
        review["findings"] = [{"severity": "P2", "path": "apps/api/payments.py",
                               "line": 9, "description": "Missing informative log"}]
        self.assertTrue(reviewer.validate_decision(review, ["apps/api/payments.py"]))

    def test_model_block_never_approves(self):
        review = self.sample()
        review["decision"] = "BLOCK"
        self.assertFalse(reviewer.validate_decision(review, ["apps/api/payments.py"]))

    def test_no_risks_or_summary_blocks(self):
        for key, value in (("risks_checked", []), ("summary", "")):
            review = self.sample()
            review[key] = value
            with self.subTest(key=key), self.assertRaises(reviewer.ReviewBlocked):
                reviewer.validate_decision(review, ["apps/api/payments.py"])

    def test_pending_and_failed_ci_blocks(self):
        values = [
            {"check_runs": [{"name": "API", "status": "in_progress", "conclusion": None}]},
            {"check_runs": [{"name": "API", "status": "completed", "conclusion": "failure"}]},
            {"check_runs": []},
        ]
        for payload in values:
            with self.subTest(payload=payload):
                with patch.object(reviewer, "github", return_value=payload):
                    with self.assertRaises(reviewer.ReviewBlocked):
                        reviewer.verified_checks(REPO, "test-token", SHA)

    def test_successful_and_optional_skipped_ci(self):
        payload = {"check_runs": [
            {"name": "API", "status": "completed", "conclusion": "success"},
            {"name": "optional", "status": "completed", "conclusion": "skipped"},
            {"name": "ChatGPT R3 agent", "status": "in_progress", "conclusion": None},
        ]}
        with patch.object(reviewer, "github", return_value=payload):
            checks = reviewer.verified_checks(REPO, "test-token", SHA)
        self.assertEqual(["API", "optional"], [c["name"] for c in checks])

    def test_draft_or_fork_or_self_authored_pr_rejected(self):
        pr = {"state": "open", "draft": False,
              "base": {"ref": "main"},
              "head": {"sha": SHA, "repo": {"full_name": REPO}},
              "user": {"login": "implementer"}}
        for mutation in (
            {"draft": True}, {"head": {"sha": SHA, "repo": {"full_name": "fork/rodada"}}},
            {"user": {"login": BOT}}, {"base": {"ref": "other"}},
        ):
            bad = dict(pr, **mutation)
            with patch.object(reviewer, "github", return_value=bad):
                with self.subTest(bad=mutation), self.assertRaises(reviewer.ReviewBlocked):
                    reviewer.get_pr_and_files(REPO, "token", 209, SHA, BOT)

    def test_missing_patch_or_binary_fails_closed(self):
        records = [{"filename": "apps/api/payments.py", "status": "modified"}]
        with self.assertRaises(reviewer.ReviewBlocked):
            reviewer.prepare_context(REPO, "token", records, SHA)

    def test_existing_approved_app_is_idempotent(self):
        data = [{"state": "APPROVED", "commit_id": SHA,
                 "user": {"login": BOT}}]
        with patch.object(reviewer, "github", return_value=data):
            self.assertTrue(reviewer.existing_approval(REPO, "token", 209, SHA, BOT))
        with patch.object(reviewer, "github", return_value=[]):
            self.assertFalse(reviewer.existing_approval(REPO, "token", 209, SHA, BOT))


if __name__ == "__main__":
    unittest.main()
