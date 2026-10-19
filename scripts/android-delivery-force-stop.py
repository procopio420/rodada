"""Real delivery POST/ACK-loss proof using the issue106 emulator/process pattern.
Requires installed debug APK pointing at loopback18135 and the local fault proxy.
Config contains synthetic test runner values only; never print it or use production.
"""
import argparse,json,re,subprocess
from pathlib import Path

METHOD="committedDeliverySurvivesActualForceStop"
ROOT=Path(__file__).resolve().parents[1]
COUNT_CHECKER=ROOT/"scripts/lib/android-instrumentation-result.sh"

def validated_config(cfg):
    if not isinstance(cfg,dict) or set(cfg)!={"venue","operator","testPin"}:
        raise ValueError("Config must contain only venue, operator and testPin; runner controls are reserved")
    if (not all(isinstance(v,str) for v in cfg.values())
            or not re.fullmatch(r"spec033-[a-z0-9-]+",cfg["venue"])
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9@._+-]*",cfg["operator"])
            or not re.fullmatch(r"[0-9]{4,12}",cfg["testPin"])):
        raise ValueError("Disposable Spec033 test runner values required")
    return cfg

def phase_succeeded(output,returncode):
    # Reuse the permanent exact-count/crash checker from PR236, plus explicit
    # method/status validation: assumptions (-4) must never masquerade as PASS.
    checked=subprocess.run(["bash","-c",'source "$1"; android_instrumentation_succeeded "$2" 1',
        "check",str(COUNT_CHECKER),output],capture_output=True)
    codes=[int(v) for v in re.findall(r"^INSTRUMENTATION_STATUS_CODE: *(-?[0-9]+)\s*$",output,re.M)]
    methods=[v.strip() for v in re.findall(r"^INSTRUMENTATION_STATUS: test=(.*)$",output,re.M)]
    return (returncode==0 and checked.returncode==0 and codes==[1,0]
        and methods==[METHOD,METHOD] and "INSTRUMENTATION_CODE: -1" in output)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--config",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--adb",default="adb")
    parser.add_argument("--serial",default="emulator-5558")
    args=parser.parse_args()
    try:cfg=validated_config(json.loads(args.config.read_text()))
    except ValueError as error:raise SystemExit(str(error))
    args.output.mkdir(parents=True,exist_ok=True)
    adb=[args.adb,"-s",args.serial]
    app="com.rodada.attendance"
    marker_name="delivery-real-force-stop.json"
    def command(*items):
        return subprocess.run(adb+list(items),capture_output=True,text=True)
    def marker_exists():
        created=command("shell","run-as",app,"mkdir","-p","files")
        listed=command("shell","run-as",app,"ls","files")
        if created.returncode or listed.returncode:
            raise SystemExit("Cannot verify private test marker state")
        return marker_name in listed.stdout.splitlines()
    def phase(name):
        cmd=adb+["shell","am","instrument","-w","-r","-e","class",
            "com.rodada.attendance.operations.LiveDeliveryRecoveryTest#"+METHOD,
            "-e","liveDeliveryRecovery","true","-e","forceStopPhase",name]
        for k,v in cfg.items():cmd += ["-e",k,v]
        cmd += [app+".test/androidx.test.runner.AndroidJUnitRunner"]
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
        output=result.stdout+result.stderr
        (args.output/(name+".log")).write_text(output)
        if not phase_succeeded(output,result.returncode):
            raise SystemExit("Instrumentation phase failed or skipped: "+name+"; see sanitized output log")
    if marker_exists():
        raise SystemExit("Existing process evidence must be recovered, not overwritten by another prepare")
    phase("prepare")
    # Same live-process requirement as scripts/android-force-stop-recovery.sh.
    started=command("shell","am","start","-W","-n",app+"/.MainActivity")
    if started.returncode:raise SystemExit("Cannot start actual application for force-stop")
    pid=command("shell","pidof",app).stdout.strip()
    if not pid:raise SystemExit("No running application; force-stop proof invalid")
    marker=command("shell","run-as",app,"cat","files/"+marker_name)
    if marker.returncode:raise SystemExit("Fresh process proof marker missing")
    proof=json.loads(marker.stdout)
    stopped=command("shell","am","force-stop",app)
    if stopped.returncode or command("shell","pidof",app).stdout.strip():
        raise SystemExit("Application did not exit after force-stop")
    phase("recover")
    if marker_exists():raise SystemExit("Recovery did not remove original process proof marker")
    (args.output/"process-proof.json").write_text(json.dumps({
        "prepare_pid":proof["pid"],"running_pid_before_force_stop":pid,
        "process_absent_after_force_stop":True,"task_id":proof["task"],
        "intent_fingerprint":proof["fingerprint"],"item_id":proof["item"],
        "result":"PASS; canonical DONE/DELIVERED, same encrypted intent and one POST"},indent=2))
    print("PASS: real committed delivery survived ACK loss and actual force-stop; one POST.")

if __name__=="__main__":main()
