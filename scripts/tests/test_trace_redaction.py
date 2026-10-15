import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location("redaction", Path(__file__).resolve().parents[1] / "sanitize-cross-surface-traces.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TraceRedactionTests(unittest.TestCase):
    def test_headers_nested_credentials_and_trace_pin(self):
        result = module.redact({"headers": [{"name": "Set-Cookie", "value": "opaque-session"}], "body": '{"session_token":"opaque-secret"}', "params": {"value": "2468"}})
        self.assertNotIn("opaque-session", str(result))
        self.assertNotIn("opaque-secret", str(result))
        self.assertNotIn("2468", str(result))

    def test_api_request_context_textual_headers(self):
        message = "→ POST /orders\n  Cookie: opaque-session=value; another=secret\n  authorization: Bearer opaque-token\n  X-Guest-Session: opaque-guest\n← 201 Created"
        result = module.redact({"type": "log", "message": message})["message"]
        for secret in ("opaque-session", "another=secret", "opaque-token", "opaque-guest"):
            self.assertNotIn(secret, result)
        self.assertIn("201 Created", result)
        self.assertEqual(result.count("[REDACTED]"), 3)

    def test_ids_and_binary_artifacts_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            source, target = Path(directory) / "raw.zip", Path(directory) / "redacted.zip"
            with zipfile.ZipFile(source, "w") as z:
                z.writestr("1.trace", '{"tab_id":"stable-id","pin":"2468"}\n')
                z.writestr("image.png", b"\x89PNG\xff\0")
            module.export(source, target)
            with zipfile.ZipFile(target) as z:
                self.assertIn(b"stable-id", z.read("1.trace"))
                self.assertNotIn(b"2468", z.read("1.trace"))
                self.assertEqual(z.read("image.png"), b"\x89PNG\xff\0")
            with zipfile.ZipFile(source) as z:
                self.assertIn(b"2468", z.read("1.trace"))
