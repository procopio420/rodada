"""Run isolated native freshness tests without printing runner secrets or clearing app data."""
import argparse,json,re,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--adb',default='adb');p.add_argument('--serial',default='emulator-5558');a=p.parse_args()
cfg=json.loads(a.config.read_text())
if set(cfg)!={'venue','operator','testPin'} or not cfg['venue'].startswith('spec033-'):raise SystemExit('Dedicated synthetic runner config required')
a.output.mkdir(parents=True,exist_ok=True)
for name,classes,extra in [('live','LiveDeliveryFreshnessTest',['-e','liveDeliveryFreshness','true']),('ui','TableReleaseTest,AttendanceNowUx2Test,NowQueuesTest,TablePresentationInstrumentedTest',[])]:
 selected=','.join('com.rodada.attendance.operations.'+c for c in classes.split(','))
 cmd=[a.adb,'-s',a.serial,'shell','am','instrument','-w','-r','-e','class',selected]+extra
 if name=='live':
  for k,v in cfg.items():cmd+=['-e',k,v]
 cmd+=['com.rodada.attendance.test/androidx.test.runner.AndroidJUnitRunner']
 res=subprocess.run(cmd,capture_output=True,text=True,timeout=240);out=res.stdout+res.stderr
 for value in cfg.values():out=out.replace(value,'[synthetic]')
 (a.output/(name+'.log')).write_text(out)
 expected=3 if name=='live' else 19
 if res.returncode or not re.search(r'OK \('+str(expected)+r' tests?\)',out) or 'INSTRUMENTATION_CODE: -1' not in out or re.search(r'FAILURES!!!|INSTRUMENTATION_FAILED|Process crashed|INSTRUMENTATION_STATUS_CODE: -(2|3|4)',out):raise SystemExit('Test failed: '+name+'; see sanitized log')
print('PASS: real HTTP/PG freshness and native UI guards; no app data cleared.')
