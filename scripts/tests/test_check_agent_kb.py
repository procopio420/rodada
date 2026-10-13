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

    def test_skill_manifests_and_claude_discovery(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            name = "rodada-django-api"
            for folder in kb.SKILL_ROOTS:
                skill_file = root / folder / name / "SKILL.md"
                skill_file.parent.mkdir(parents=True)
                body = "Procedure: inspect specs, implement, and validate tests."
                if folder == ".claude/skills":
                    body += f" [canonical](../../../.agents/skills/{name}/SKILL.md)"
                skill_file.write_text(
                    f"---\nname: {name}\ndescription: Use for Django and DRF tasks.\n---\n\n{body}\n",
                    encoding="utf-8",
                )
            self.assertEqual(kb.check_skill_manifests(root, (name,)), [])
            (root / ".claude" / "skills" / name / "SKILL.md").write_text(
                "---\nname: mismatch\ndescription: Too short\n---\n\nBad",
                encoding="utf-8",
            )
            errors = kb.check_skill_manifests(root, (name,))
            self.assertTrue(any("name must match" in error for error in errors))
            self.assertTrue(any("missing canonical" in error for error in errors))

    def test_missing_skill_and_missing_frontmatter(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            name = "rodada-nextjs-web"
            file = root / ".agents" / "skills" / name / "SKILL.md"
            file.parent.mkdir(parents=True)
            file.write_text("# no front matter\n", encoding="utf-8")
            errors = kb.check_skill_manifests(root, (name,))
            self.assertTrue(any("missing YAML" in error for error in errors))
            self.assertTrue(any("missing required skill" in error for error in errors))

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
