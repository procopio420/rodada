import subprocess,time,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[4]
out=root/'docs/development/evidence/spec033-native-shell';out.mkdir(exist_ok=True,parents=True)
adb=['/home/lucas/Android/Sdk/platform-tools/adb','-s','emulator-5558']
def run(args): return subprocess.run(adb+args,capture_output=True,text=True,check=True)
for w,h in [(390,844),(360,800),(430,932)]:
 run(['shell','wm','size',f'{w*3}x{h*3}']);run(['shell','wm','density','480']);run(['shell','settings','put','system','font_scale','1.0']);time.sleep(2)
 run(['shell','am','force-stop','com.rodada.attendance']);run(['shell','pm','clear','com.rodada.attendance'])
 for stem in ['live-agora-service','live-shell-tables','live-shell-table','live-shell-tab','live-shell-catalog','live-shell-review']:
  run(['shell','rm','-f',f'/data/local/tmp/rodada-critical-evidence/{stem}-w{w*3}-f100.png'])
 result=run(['shell','am','instrument','-w','-r','-e','liveAgora','true','-e','shellJourney','true','-e','venueSlug','spec033-native-shell-parity','-e','tableId','e1bb3718-21db-4973-949f-7ead5111f790','-e','expectedApiBaseUrl','http://10.0.2.2:18131/','-e','class','com.rodada.attendance.operations.LiveAgoraUx2Test','com.rodada.attendance.test/androidx.test.runner.AndroidJUnitRunner'])
 (out/f'live-{w}.txt').write_text(result.stdout+result.stderr)
 print(w,result.stdout[-180:],flush=True)
 files=run(['shell','ls','/data/local/tmp/rodada-critical-evidence/']).stdout.splitlines()
 for f in files:
  if f.startswith(('live-shell-','live-agora-service')) and f.endswith(f'w{w*3}-f100.png'):
   run(['pull',f'/data/local/tmp/rodada-critical-evidence/{f}',str(out/f)])
 if 'OK (1 test)' not in result.stdout: raise SystemExit(1)
