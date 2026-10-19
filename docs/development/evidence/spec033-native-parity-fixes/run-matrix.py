import subprocess,pathlib,json,time,os
adb=str(pathlib.Path(os.environ.get('ANDROID_HOME', str(pathlib.Path.home()/'Android/Sdk')))/'platform-tools/adb'); root=pathlib.Path(__file__).resolve().parents[4]; out=root/'docs/development/evidence/spec033-native-parity-fixes'; android=root/'apps/attendance-android'
def run(*args): return subprocess.run([adb,'-s','emulator-5558',*args],check=True,capture_output=True,text=True).stdout
run('install','-r',str(android/'app/build/outputs/apk/debug/app-debug.apk'))
run('install','-r',str(android/'app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'))
results=[]
try:
 for width in (360,390,430):
  for font in ('1.0','2.0'):
   label=f'w{width}-f{font}'; folder=out/label; folder.mkdir(exist_ok=True)
   run('shell','wm','density','160'); run('shell','wm','size',f'{width}x900'); run('shell','settings','put','system','font_scale',font)
   time.sleep(2)
   output=run('shell','am','instrument','-w','-e','class','com.rodada.attendance.operations.Ux2TabPagesTest#prototypeMarinaCatalogAndSummary,com.rodada.attendance.operations.Ux2TabPagesTest#quantityPaintKeepsPrototypeSizeAndExpandedTouchTarget,com.rodada.attendance.operations.Ux2TabPagesTest#restoredNoteOnlyDraftRetainsEditing,com.rodada.attendance.operations.Ux2AccountPagesTest#fullReceiptOffersCloseAndKeepOpenWithOriginalCashPoint','com.rodada.attendance.test/androidx.test.runner.AndroidJUnitRunner')
   (folder/'instrumentation.txt').write_text(output)
   for stem in ('prototype-marina-catalog','prototype-marina-summary','ux2-receipt-full'):
    path=f'/data/local/tmp/rodada-critical-evidence/{stem}-w{width}-f{int(float(font)*100)}.png'
    run('pull',path,str(folder))
   results.append({'width':width,'font':font,'passed':'OK (4 tests)' in output}); (out/'results.json').write_text(json.dumps(results,indent=2))
finally:
 run('shell','wm','density','480');run('shell','wm','size','1170x2532');run('shell','settings','put','system','font_scale','1.0')

if len(results) != 6 or not all(result["passed"] for result in results):
 raise SystemExit("Native parity matrix failed; inspect instrumentation.txt")
