"""Capture freshness and release guards at 360/390/430dp, font scales1/2.
Run from repository root with the test APK installed; never clears app data.
"""
import subprocess,pathlib,re,os
adb=os.environ.get('ADB', 'adb');dest=pathlib.Path('docs/development/evidence/spec033-native-delivery-freshness');classes='com.rodada.attendance.operations.AttendanceNowUx2Test#queueFailureKeepsLastWorkWithUnknownCountAndRecoveryRestoresIt,com.rodada.attendance.operations.TableReleaseTest#staleDispatchWhileDialogOpenBlocksRelease'
def cmd(*args):return subprocess.run([adb,'-s','emulator-5558',*args],capture_output=True,text=True,timeout=180)
try:
 for font in [1,2]:
  for width in [360,390,430]:
   assert cmd('shell','wm','size',f'{width*3}x2532').returncode==0
   assert cmd('shell','wm','density','480').returncode==0
   assert cmd('shell','settings','put','system','font_scale',str(font)).returncode==0
   r=cmd('shell','am','instrument','-w','-r','-e','class',classes,'com.rodada.attendance.test/androidx.test.runner.AndroidJUnitRunner');out=r.stdout+r.stderr
   (dest/f'matrix-{width}-font{font}.log').write_text(out)
   assert r.returncode==0 and 'OK (2 tests)' in out and 'INSTRUMENTATION_CODE: -1' in out and not re.search('FAILURES!!!|INSTRUMENTATION_FAILED|INSTRUMENTATION_STATUS_CODE: -(2|3|4)',out),(width,font)
   print(f'PASS {width}dp font{font}',flush=True)
finally:
 cmd('shell','wm','size','1170x2532');cmd('shell','wm','density','480');cmd('shell','settings','put','system','font_scale','1')
