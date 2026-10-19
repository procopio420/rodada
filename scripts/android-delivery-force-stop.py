"""Real delivery POST/ACK-loss proof using the issue106 emulator/process pattern.
Requires installed debug APK pointing at loopback18135 and the local fault proxy.
Config contains synthetic test runner values only; never print it or use production.
"""
import argparse,json,re,subprocess
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument("--config",type=Path,required=True)
parser.add_argument("--output",type=Path,required=True)
parser.add_argument("--adb",default="adb")
parser.add_argument("--serial",default="emulator-5558")
args=parser.parse_args()
cfg=json.loads(args.config.read_text())
if not cfg["venue"].startswith("spec033-"):
    raise SystemExit("Disposable Spec033 test venue required")
args.output.mkdir(parents=True,exist_ok=True)
adb=[args.adb,"-s",args.serial]
app="com.rodada.attendance"
def command(*items):
    return subprocess.run(adb+list(items),capture_output=True,text=True)
def phase(name):
    cmd=adb+["shell","am","instrument","-w","-r","-e","class",
        "com.rodada.attendance.operations.LiveDeliveryRecoveryTest#committedDeliverySurvivesActualForceStop",
        "-e","liveDeliveryRecovery","true","-e","forceStopPhase",name]
    for k,v in cfg.items():cmd += ["-e",k,v]
    cmd += [app+".test/androidx.test.runner.AndroidJUnitRunner"]
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
    output=result.stdout+result.stderr
    (args.output/(name+".log")).write_text(output)
    if (result.returncode or not re.search(r"OK \(1 test\)",output)
            or "INSTRUMENTATION_CODE: -1" not in output
            or re.search(r"FAILURES!!!|INSTRUMENTATION_FAILED|Process crashed|INSTRUMENTATION_STATUS_CODE: -(2|3)",output)):
        raise SystemExit("Instrumentation phase failed: "+name+"; see sanitized output log")
phase("prepare")
# Same live-process requirement as scripts/android-force-stop-recovery.sh.
started=command("shell","am","start","-W","-n",app+"/.MainActivity")
if started.returncode:raise SystemExit("Cannot start actual application for force-stop")
pid=command("shell","pidof",app).stdout.strip()
if not pid:raise SystemExit("No running application; force-stop proof invalid")
marker=command("shell","run-as",app,"cat","files/delivery-real-force-stop.json")
if marker.returncode:raise SystemExit("Original process proof marker missing")
proof=json.loads(marker.stdout)
stopped=command("shell","am","force-stop",app)
if stopped.returncode or command("shell","pidof",app).stdout.strip():
    raise SystemExit("Application did not exit after force-stop")
phase("recover")
(args.output/"process-proof.json").write_text(json.dumps({
    "prepare_pid":proof["pid"],"running_pid_before_force_stop":pid,
    "process_absent_after_force_stop":True,"task_id":proof["task"],
    "intent_fingerprint":proof["fingerprint"],"item_id":proof["item"],
    "result":"PASS; canonical DONE/DELIVERED, same encrypted intent and one POST"},indent=2))
print("PASS: real committed delivery survived ACK loss and actual force-stop; one POST.")
