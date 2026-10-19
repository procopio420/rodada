"""Regression for assumption skips and config overrides found in R3 review."""
import importlib.util
import pathlib
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("delivery_process_runner",ROOT/"scripts/android-delivery-force-stop.py")
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

class DeliveryForceStopRunnerTest(unittest.TestCase):
    def transcript(self):
        return (ROOT/"docs/development/evidence/spec033-native-delivery-recovery/force-stop/prepare.log").read_text()
    def test_actual_recorded_phase_is_accepted(self):
        self.assertTrue(runner.phase_succeeded(self.transcript(),0))
    def test_assumption_and_failure_codes_cannot_pass_with_ok_marker(self):
        for code in (-1,-2,-3,-4):
            with self.subTest(code=code):
                self.assertFalse(runner.phase_succeeded(self.transcript().replace("INSTRUMENTATION_STATUS_CODE: 0",f"INSTRUMENTATION_STATUS_CODE: {code}"),0))
    def test_missing_or_wrong_method_completion_is_not_a_pass(self):
        self.assertFalse(runner.phase_succeeded(self.transcript().replace(runner.METHOD,"otherMethod"),0))
        self.assertFalse(runner.phase_succeeded(self.transcript().replace("INSTRUMENTATION_STATUS_CODE: 0", ""),0))
    def test_failure_after_success_and_bad_exit_are_rejected(self):
        self.assertFalse(runner.phase_succeeded(self.transcript()+"\nINSTRUMENTATION_FAILED: crash",0))
        self.assertFalse(runner.phase_succeeded(self.transcript(),1))
    def test_runner_control_arguments_cannot_be_overridden(self):
        valid={"venue":"spec033-runner-test","operator":"synthetic","testPin":"0000"}
        self.assertEqual(valid,runner.validated_config(valid))
        for name in ("liveDeliveryRecovery","forceStopPhase","class"):
            with self.subTest(name=name),self.assertRaises(ValueError):
                runner.validated_config({**valid,name:"false"})
    def test_non_test_or_shell_control_values_are_rejected(self):
        valid={"venue":"spec033-runner-test","operator":"synthetic","testPin":"0000"}
        for name,value in (("venue","production"),("operator","synthetic -e class other"),("testPin",False)):
            with self.subTest(name=name),self.assertRaises(ValueError):
                runner.validated_config({**valid,name:value})

if __name__=="__main__":unittest.main()
