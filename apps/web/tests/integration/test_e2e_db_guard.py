"""Stdlib regressions for the test-only PostgreSQL reset coordinator."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from e2e_db_guard import _sqlstate, file_lock, retry_transient_reset


class FakePsycopgDeadlock(Exception):
    sqlstate = "40P01"


class FakePsycopgLockTimeout(Exception):
    pgcode = "55P03"


class ResetGuardTests(unittest.TestCase):
    def test_shared_lock_waits_for_exclusive_reset_across_processes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "reset.lock"
            script = (
                "import sys\\n"
                "from pathlib import Path\\n"
                f"sys.path.insert(0, {str(Path(__file__).resolve().parent)!r})\\n"
                "from e2e_db_guard import file_lock\\n"
                "with file_lock(Path(sys.argv[1]), exclusive=False):\\n"
                "    print('acquired', flush=True)\\n"
            )
            with file_lock(path, exclusive=True):
                process = subprocess.Popen(
                    [sys.executable, "-c", script, str(path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                try:
                    time.sleep(0.15)
                    self.assertIsNone(process.poll(), "Reader must block while reset holds lock")
                finally:
                    # Process finishes as soon as this writer lock is released.
                    pass
            stdout, stderr = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(stdout.strip(), "acquired")

    def test_retries_deadlock_or_lock_timeout_only(self):
        for problem in (FakePsycopgDeadlock(), FakePsycopgLockTimeout()):
            calls = []

            def operation():
                calls.append(True)
                if len(calls) < 3:
                    raise RuntimeError("Django wrapper") from problem

            with patch("e2e_db_guard.time.sleep") as sleeper:
                retry_transient_reset(operation)
            self.assertEqual(len(calls), 3)
            self.assertEqual(sleeper.call_count, 2)

    def test_unknown_or_persistent_db_errors_fail_closed(self):
        with self.assertRaisesRegex(RuntimeError, "unknown"):
            retry_transient_reset(lambda: (_ for _ in ()).throw(RuntimeError("unknown")))
        with patch("e2e_db_guard.time.sleep"):
            with self.assertRaises(FakePsycopgDeadlock):
                retry_transient_reset(
                    lambda: (_ for _ in ()).throw(FakePsycopgDeadlock()), max_attempts=2
                )

    def test_extracts_nested_psycopg_sqlstate(self):
        try:
            raise RuntimeError("Django wrapper") from FakePsycopgDeadlock()
        except RuntimeError as e:
            self.assertEqual(_sqlstate(e), "40P01")
        self.assertIsNone(_sqlstate(ValueError("not database")))


if __name__ == "__main__":
    unittest.main()
