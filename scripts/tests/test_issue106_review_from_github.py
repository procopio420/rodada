"""Unit tests for trusted GitHub R3 provenance; no network or real account requests."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "issue106_review_from_github",
    Path(__file__).resolve().parents[1] / "issue106_review_from_github.py",
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
SHA = "a" * 40
REPO = "procopio420/rodada"


class ReviewProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.pr = {
            "head": {"sha": SHA, "repo": {"full_name": REPO}},
            "user": {"login": "author"},
        }
        self.review = {
            "id": 123, "state": "APPROVED", "commit_id": SHA,
            "body": "R3: PASS\nP0/P1: 0\nVerified the risk checklist.",
            "submitted_at": "2026-10-16T00:00:00Z",
            "user": {"login": "independent-human", "type": "User"},
        }

    def find(self, reviews=None, pr=None, sha=SHA):
        reviews = reviews if reviews is not None else [self.review]
        pr = pr if pr is not None else self.pr
        def fetch(path):
            if path == "/pulls/106":
                return pr
            if path.startswith("/pulls/106/reviews?"):
                return reviews if path.endswith("page=1") else []
            raise AssertionError(path)
        return module.find_review(REPO, 106, sha, fetch)

    def test_exact_head_independent_r3(self):
        proof = self.find()
        self.assertEqual(SHA, proof["sha"])
        self.assertEqual(0, proof["open_p0_p1"])
        self.assertTrue(proof["independent"])
        self.assertIn("pullrequestreview-123", proof["reference"])

    def test_self_approval_rejected(self):
        self.review["user"]["login"] = "author"
        with self.assertRaises(module.ReviewBlocked):
            self.find()

    def test_review_of_earlier_commit_rejected(self):
        self.review["commit_id"] = "b" * 40
        with self.assertRaises(module.ReviewBlocked):
            self.find()

    def test_pr_head_mismatch_rejected(self):
        with self.assertRaises(module.ReviewBlocked):
            self.find(sha="b" * 40)

    def test_no_claim_of_zero_findings_rejected(self):
        self.review["body"] = "R3: PASS\nP0/P1: unknown"
        with self.assertRaises(module.ReviewBlocked):
            self.find()

    def test_later_changes_requested_blocks_previous_approval(self):
        dissent = dict(self.review, id=124, state="CHANGES_REQUESTED")
        dissent["user"] = {"login": "another-reviewer", "type": "User"}
        with self.assertRaises(module.ReviewBlocked):
            self.find(reviews=[self.review, dissent])

    def test_dismissed_approval_rejected(self):
        self.review["state"] = "DISMISSED"
        with self.assertRaises(module.ReviewBlocked):
            self.find()

    def test_fork_pr_rejected(self):
        self.pr["head"]["repo"]["full_name"] = "someone-else/rodada"
        with self.assertRaises(module.ReviewBlocked):
            self.find()


if __name__ == "__main__":
    unittest.main()
