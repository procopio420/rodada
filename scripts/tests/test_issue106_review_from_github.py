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

    def test_comment_or_pending_does_not_clear_another_reviewers_veto(self):
        dissent = dict(self.review, id=124, state="CHANGES_REQUESTED",
                       user={"login":"another-reviewer", "type":"User"})
        for state in ("COMMENTED", "PENDING"):
            with self.subTest(state=state), self.assertRaises(module.ReviewBlocked):
                self.find(reviews=[self.review, dissent, dict(dissent, id=125, state=state)])

    def test_comment_does_not_discard_existing_approval(self):
        proof = self.find(reviews=[self.review, dict(self.review, id=124, state="COMMENTED")])
        self.assertIn("pullrequestreview-123", proof["reference"])

    def test_explicit_approval_or_dismissal_resolves_previous_veto(self):
        dissent = dict(self.review, id=124, state="CHANGES_REQUESTED",
                       user={"login":"another-reviewer", "type":"User"})
        for state in ("APPROVED", "DISMISSED"):
            with self.subTest(state=state):
                self.assertTrue(self.find(reviews=[self.review, dissent, dict(dissent, id=125, state=state)])["independent"])

    def test_dismissed_approval_rejected(self):
        self.review["state"] = "DISMISSED"
        with self.assertRaises(module.ReviewBlocked):
            self.find()

    def test_fork_pr_rejected(self):
        self.pr["head"]["repo"]["full_name"] = "someone-else/rodada"
        with self.assertRaises(module.ReviewBlocked):
            self.find()


    def agent_fixture(self, *, paths=None, login="r3-reviewer[bot]", sha=SHA):
        paths = paths if paths is not None else [
            "apps/api/modules/ledger/services.py",
            "apps/web/tests/cross-surface/financial.spec.ts",
            "apps/attendance-android/app/src/main/java/Orders.kt",
        ]
        evidence_url = f"https://github.com/{REPO}/pull/106#issuecomment-456"
        review = dict(
            self.review, id=987,
            body=f"R3: PASS\nP0/P1: 0\nR3-Agent-Context: isolated\nR3-Evidence: {evidence_url}",
            user={"login": login, "type": "Bot"},
        )
        comment = {
            "user": {"login": login},
            "html_url": evidence_url,
            "body": f"R3-Reviewed-SHA: {sha}\nR3-Tests-Checked: native + payments SQL regression\nR3-Risks-Checked: concurrency, replay, auth and tenant",
        }
        def fetch(path):
            if path == "/pulls/106":
                return self.pr
            if path.startswith("/pulls/106/reviews?"):
                return [review] if path.endswith("page=1") else []
            if path == "/pulls/106/files?per_page=100&page=1":
                return [{"filename": name} for name in paths]
            if path == "/issues/comments/456":
                return comment
            raise AssertionError(path)
        registry = module.parse_qualified_agents(
            '{"r3-reviewer[bot]":{"capabilities":["backend","payments","web","android","security"],'
            '"expires_on":"2027-10-16","sponsor":"engineering-lead"}}'
        )
        return review, comment, registry, fetch

    def test_qualified_app_bot_approved_with_scoped_evidence(self):
        _review, _comment, registry, fetch = self.agent_fixture()
        proof = module.find_review(REPO, 106, SHA, fetch, qualified_agents=registry)
        self.assertEqual("qualified-agent", proof["reviewer_kind"])
        self.assertEqual("github-api-qualified-agent-exact-head", proof["source"])
        self.assertEqual("engineering-lead", proof["qualification_sponsor"])
        self.assertEqual(["android", "backend", "payments", "web"], proof["reviewed_scopes"])
        self.assertIn("issuecomment-456", proof["evidence_url"])

    def test_unknown_bot_cannot_approve(self):
        _review, _comment, _registry, fetch = self.agent_fixture()
        with self.assertRaises(module.ReviewBlocked):
            module.find_review(REPO, 106, SHA, fetch)

    def test_expired_qualification_cannot_approve(self):
        _review, _comment, registry, fetch = self.agent_fixture()
        with self.assertRaises(module.ReviewBlocked):
            module.find_review(REPO, 106, SHA, fetch, qualified_agents=registry,
                               today=__import__("datetime").date(2028, 1, 1))

    def test_bot_missing_required_capability_cannot_approve(self):
        _review, _comment, registry, fetch = self.agent_fixture()
        registry["r3-reviewer[bot]"]["capabilities"].discard("payments")
        with self.assertRaises(module.ReviewBlocked):
            module.find_review(REPO, 106, SHA, fetch, qualified_agents=registry)

    def test_bot_self_approval_cannot_approve(self):
        _review, _comment, registry, fetch = self.agent_fixture()
        self.pr["user"]["login"] = "r3-reviewer[bot]"
        with self.assertRaises(module.ReviewBlocked):
            module.find_review(REPO, 106, SHA, fetch, qualified_agents=registry)

    def test_bot_evidence_rejects_wrong_author_or_sha(self):
        review, comment, registry, fetch = self.agent_fixture()
        for mutator in (
            lambda: comment["user"].update(login="someone-else"),
            lambda: comment.update(body=comment["body"].replace(SHA, "b" * 40)),
            lambda: review.update(body="R3: PASS\nP0/P1: 0\nR3-Agent-Context: isolated"),
            lambda: review.update(commit_id="b" * 40),
        ):
            with self.subTest(mutator=mutator):
                review["body"] = (f"R3: PASS\nP0/P1: 0\nR3-Agent-Context: isolated\n"
                                  f"R3-Evidence: https://github.com/{REPO}/pull/106#issuecomment-456")
                review["commit_id"] = SHA
                comment["user"]["login"] = "r3-reviewer[bot]"
                comment["body"] = (f"R3-Reviewed-SHA: {SHA}\nR3-Tests-Checked: SQL and native\n"
                                   "R3-Risks-Checked: money and replay")
                mutator()
                with self.assertRaises(module.ReviewBlocked):
                    module.find_review(REPO, 106, SHA, fetch, qualified_agents=registry)

    def test_bot_changes_requested_veto_overrides_approval(self):
        review, _comment, registry, orig_fetch = self.agent_fixture()
        veto = dict(review, id=991, state="CHANGES_REQUESTED",
                    user={"login": "another-reviewer", "type": "User"})
        def fetch(path):
            if path.startswith("/pulls/106/reviews?"):
                return [review, veto, dict(veto, id=992, state="COMMENTED")]
            return orig_fetch(path)
        with self.assertRaises(module.ReviewBlocked):
            module.find_review(REPO, 106, SHA, fetch, qualified_agents=registry)

    def test_bot_qualification_rejects_fake_and_malformed_registries(self):
        for raw in (
            "not json", "[]", '{"any-user":{"capabilities":["security"],"expires_on":"2027-01-01","sponsor":"lead"}}',
            '{"github-actions[bot]":{"capabilities":["superuser"],"expires_on":"2027-01-01","sponsor":"lead"}}',
            '{"r3-reviewer[bot]":{"capabilities":["security"],"expires_on":"invalid","sponsor":"lead"}}',
            '{"r3-reviewer[bot]":{"capabilities":[],"expires_on":"2027-01-01","sponsor":"lead"}}',
        ):
            with self.subTest(raw=raw), self.assertRaises(module.ReviewBlocked):
                module.parse_qualified_agents(raw)

    def test_bot_qualification_pagination_and_empty_files_fail_closed(self):
        _review, _comment, registry, original = self.agent_fixture(paths=[])
        with self.assertRaises(module.ReviewBlocked):
            module.find_review(REPO, 106, SHA, original, qualified_agents=registry)


if __name__ == "__main__":
    unittest.main()
