import os,subprocess,time,json,sys
from pathlib import Path
import django;django.setup()
sys.path.insert(0,'scripts')
from cross_surface_fixture import require_connected_database,database_instance_identity
from django.db import connection
from django.utils import timezone
from modules.guest_access.models import GuestSession
require_connected_database(connection)
out=Path('/home/lucas/.cache/rodada033-origin-evidence'); f=json.loads((out/'fixture.json').read_text());assert f['database_instance_id']==database_instance_identity(connection)
adb=['/home/lucas/Android/Sdk/platform-tools/adb','-s','emulator-5558']
def sh(*a,check=True):return subprocess.run(adb+list(a),capture_output=True,text=True,check=check)
for _ in range(90):
 if sh('shell','getprop','sys.boot_completed',check=False).stdout.strip()=='1':break
 time.sleep(2)
else:raise SystemExit('Emulator boot timeout')
for apk in ('debug/app-debug.apk','androidTest/debug/app-debug-androidTest.apk'):
 print(sh('install','-r','/home/lucas/projects/rodada/ux2-android-origin-fix/apps/attendance-android/app/build/outputs/apk/'+apk).stdout,flush=True)
results=[]
for width,font in [(360,1),(390,1),(430,1),(360,2),(390,2),(430,2)]:
 label=f'w{width}-f{font}';d=out/label;d.mkdir(exist_ok=False)
 sh('shell','wm','density','160');sh('shell','wm','size',f'{width}x900');sh('shell','settings','put','system','font_scale',str(font))
 sh('shell','pm','clear','com.rodada.attendance')
 GuestSession.objects.filter(pk=f['guest_session_id'],tab_id=f['fallback_tab_id']).update(revoked_at=None,revoked_reason='')
 with (d/'instrumentation.txt').open('w') as log:
  proc=subprocess.Popen(adb+['shell','am','instrument','--user','0','-w','-r','-e','class','com.rodada.attendance.operations.LiveAgoraUx2Test','-e','liveAgora','true','-e','expectedApiBaseUrl','http://10.0.2.2:18131/','-e','serviceTaskId',f['service_task_id'],'-e','revokeBeforeOpen','true','-e','refreshBeforeTask','true','-e','fallbackTabName',"'Origin fallback A'",'com.rodada.attendance.test/androidx.test.runner.AndroidJUnitRunner'],stdout=log,stderr=subprocess.STDOUT)
  deadline=time.monotonic()+180;revoked=False
  while proc.poll() is None and time.monotonic()<deadline:
   if not revoked and sh('shell','run-as','com.rodada.attendance','test','-f','files/task-readback-ready',check=False).returncode==0:
    count=GuestSession.objects.filter(pk=f['guest_session_id'],tab_id=f['fallback_tab_id']).update(revoked_at=timezone.now(),revoked_reason='isolated native readback test');assert count==1
    sh('shell','run-as','com.rodada.attendance','touch','files/task-readback-revoked');revoked=True
   time.sleep(1)
  if proc.poll() is None:proc.terminate();proc.wait()
 logtext=(d/'instrumentation.txt').read_text(); passed='OK (1 test)' in logtext
 results.append(dict(width=width,font=font,revoked=revoked,passed=passed,exit=proc.returncode))
 print(label,results[-1],flush=True)
 sh('pull','/data/local/tmp/rodada-critical-evidence',str(d),check=False)
 sh('shell','uiautomator','dump','/sdcard/origin-window.xml',check=False);sh('pull','/sdcard/origin-window.xml',str(d/'window.xml'),check=False)
 with (d/'screen.png').open('wb') as image:subprocess.run(adb+['exec-out','screencap','-p'],stdout=image,check=True)
 (out/'results.json').write_text(json.dumps(results,indent=2))
