"""Tests for scripts/check_agent_kb.py (stdlib only)."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "check_agent_kb.py"
spec = importlib.util.spec_from_file_location("check_agent_kb", MODULE)
kb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kb)


class AgentKbTest(unittest.TestCase):
    def test_good_internal_link_and_anchors(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            source = root / "docs" / "A.md"
            target = root / "B.md"
            target.write_text("# Heading", encoding="utf-8")
            source.write_text("[Local](../B.md#heading) [Web](https://rodada.bar) [Heading](#self)", encoding="utf-8")
            errors, checked = kb.check_links(root, [source])
            self.assertEqual((errors, checked), ([], 1))

    def test_missing_file_fails_and_escape_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "docs" / "index.md"
            path.parent.mkdir()
            path.write_text("[Missing](../absent.md) [Escape](../../secrets.md)", encoding="utf-8")
            errors, checked = kb.check_links(root, [path])
            self.assertEqual(checked, 2)
            self.assertTrue(any("broken local link" in x for x in errors))
            self.assertTrue(any("escapes repository" in x for x in errors))

    def test_domain_contract_rejects_old_canonical(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in kb.CURRENT_DOMAIN_DOCS:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("Current: rodada.bar", encoding="utf-8")
            self.assertEqual(kb.check_canonical_domains(root), [])
            (root / "README.md").write_text("rodada.ai; rodada.bar", encoding="utf-8")
            errors = kb.check_canonical_domains(root)
            self.assertEqual(len(errors), 1)
            self.assertIn("README.md", errors[0])


if __name__ == "__main__":
    unittest.main()
