"""Focused pure tests for added-line quality guards (no Ruff or git needed)."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "quality" / "check_added_lines.py"
spec = importlib.util.spec_from_file_location("quality_added_lines", MODULE)
quality = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quality)


class QualityGateTests(unittest.TestCase):
    def test_additions_deletions_and_multiple_hunks(self):
        diff = """diff --git a/apps/api/test.py b/apps/api/test.py
--- a/apps/api/test.py
+++ b/apps/api/test.py
@@ -2,1 +2,2 @@
-old
+new
+another
@@ -12,0 +14,1 @@
+last
diff --git a/apps/web/page.tsx b/apps/web/page.tsx
--- /dev/null
+++ b/apps/web/page.tsx
@@ -0,0 +1,1 @@
+export default function Page() {}
"""
        additions, text = quality.added_lines(diff)
        self.assertEqual(additions["apps/api/test.py"], {2, 3, 14})
        self.assertEqual(text["apps/api/test.py"][14], "last")
        self.assertEqual(additions["apps/web/page.tsx"], {1})

    def test_web_added_rules_ignore_unchanged_lines(self):
        diff = """diff --git a/apps/web/a.ts b/apps/web/a.ts
--- a/apps/web/a.ts
+++ b/apps/web/a.ts
@@ -1,2 +1,3 @@
+// @ts-ignore
 const ok = 1
 const ignored = 3
"""
        _, source = quality.added_lines(diff)
        self.assertEqual(len(quality.web_findings(source)), 1)
        self.assertIn("TYPECHECK_BYPASS", quality.web_findings(source)[0])

    def test_ruff_gate_only_added_lines(self):
        root = Path("/tmp/rodada-quality")
        diagnostics = [
            {"filename": str(root / "apps/api/a.py"), "location": {"row": 9},
             "code": "F821", "message": "undefined name"},
            {"filename": str(root / "apps/api/a.py"), "location": {"row": 10},
             "code": "F401", "message": "unused import"},
        ]
        self.assertEqual(
            quality.ruff_findings(diagnostics, {"apps/api/a.py": {10}}, root),
            ["apps/api/a.py:10: F401: unused import"],
        )

    def test_eslint_additions_and_fatal_errors(self):
        root = Path("/tmp/rodada-quality")
        results = [{"filePath": str(root / "apps/web/app/page.tsx"),
                    "messages": [
                        {"line": 2, "ruleId": "no-unused-vars", "message": "old"},
                        {"line": 5, "ruleId": "react-hooks/exhaustive-deps",
                         "message": "new warning"},
                        {"fatal": True, "message": "unparseable file"},
                    ]}]
        count, findings = quality.eslint_findings(
            results, {"apps/web/app/page.tsx": {5}}, root
        )
        self.assertEqual(count, 3)
        self.assertEqual(len(findings), 2)
        self.assertIn("react-hooks/exhaustive-deps", findings[0])
        self.assertIn("ESLINT_FATAL", findings[1])

    def test_web_guard_rejects_secret_env_and_eval(self):
        findings = quality.web_findings({
            "apps/web/app/page.tsx": {
                1: "const x = process.env.NEXT_PUBLIC_REFRESH_TOKEN",
                2: "const y = eval(userInput)",
            },
            "apps/landing/index.html": {1: "// @ts-nocheck"},
        })
        self.assertEqual(len(findings), 2)


if __name__ == "__main__":
    unittest.main()
