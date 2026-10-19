"""Runner checks must reject synthetic green/assumption skips before calling a real run PASS."""
import contextlib
import io
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch

RUNNER = Path(__file__).with_name('android-history-session-fence.py')
METHOD = 'lateHistorySuccessAndFailureCannotFinishNewHistoryAcrossSessionGenerations'
GOOD = f'INSTRUMENTATION_STATUS: test={METHOD}\nINSTRUMENTATION_STATUS_CODE: 1\nINSTRUMENTATION_STATUS: test={METHOD}\nINSTRUMENTATION_STATUS_CODE: 0\nINSTRUMENTATION_CODE: -1\n'

class RunnerTest(unittest.TestCase):
    def execute(self, transcript=GOOD, extra=None, timeout=False):
        with tempfile.TemporaryDirectory() as folder:
            config = {'venue':'synthetic','operator':'staff-a','testPin':'111111','operatorB':'staff-b',
                      'testPinB':'222222','liveHistorySessionFence':'true'}
            if extra: config.update(extra)
            path = Path(folder)/'private.json'; path.write_text(json.dumps(config))
            output = Path(folder)/'sanitized.log'
            result = subprocess.CompletedProcess([],0,transcript,'')
            side_effect = subprocess.TimeoutExpired('private-values-must-not-print',300) if timeout else None
            with patch('sys.argv',[str(RUNNER),str(path),str(output)]), patch('subprocess.run',return_value=result,side_effect=side_effect), contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path(str(RUNNER),run_name='__main__')
    def test_exact_method_passes(self): self.execute()
    def test_assumption_skip_rejected(self):
        with self.assertRaises(SystemExit): self.execute(GOOD.replace('STATUS_CODE: 0','STATUS_CODE: -4'))
    def test_fake_ok_count_rejected(self):
        with self.assertRaises(SystemExit): self.execute('OK (1 test)\nINSTRUMENTATION_CODE: -1\n')
    def test_different_method_rejected(self):
        with self.assertRaises(SystemExit): self.execute(GOOD.replace(METHOD,'otherTest'))
    def test_reserved_argument_rejected(self):
        with self.assertRaises(SystemExit): self.execute(extra={'class':'malicious.override'})
    def test_timeout_does_not_print_private_command(self):
        with self.assertRaises(SystemExit) as caught: self.execute(timeout=True)
        self.assertNotIn('private-values-must-not-print',str(caught.exception))

if __name__ == '__main__': unittest.main()
