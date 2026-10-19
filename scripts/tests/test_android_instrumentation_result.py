"""Regression for the real CI four-test success and false success outputs."""
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PARSER = ROOT / 'scripts/lib/android-instrumentation-result.sh'


class InstrumentationResultTest(unittest.TestCase):
    def accepted(self, output, count):
        result = subprocess.run(['bash', '-c', 'source "$1"; android_instrumentation_succeeded "$2" "$3"', 'check', str(PARSER), output, str(count)], capture_output=True)
        return result.returncode == 0

    def test_actual_ci_four_test_success(self):
        # Run 39079625491, TableServiceNavigationTest: all tests passed.
        output = 'com.rodada.attendance.operations.TableServiceNavigationTest:....\n\nTime: 20.764\n\nOK (4 tests)\n'
        self.assertTrue(self.accepted(output, 4))
        self.assertFalse(self.accepted(output, 3))

    def test_zero_and_partial_class_never_pass(self):
        for output in ['OK (0 tests)', 'OK (1 test)', '', 'INSTRUMENTATION_CODE: -1']:
            self.assertFalse(self.accepted(output, 4))
        self.assertFalse(self.accepted('OK (0 tests)', 0))

    def test_singular_crlf_output(self):
        self.assertTrue(self.accepted('Time: 0.074\r\n\r\nOK (1 test)\r\n', 1))

    def test_failure_or_crash_cannot_hide_behind_success_marker(self):
        for error in ['FAILURES!!!', 'INSTRUMENTATION_FAILED: runner', 'INSTRUMENTATION_ABORTED: crash', 'INSTRUMENTATION_RESULT: shortMsg=Process crashed.', 'INSTRUMENTATION_RESULT: longMsg=java.lang.AssertionError', 'Tests failed']:
            self.assertFalse(self.accepted('OK (4 tests)\n' + error, 4))


if __name__ == '__main__':
    unittest.main()
