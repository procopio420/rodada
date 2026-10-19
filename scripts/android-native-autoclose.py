"""Run the canonical auto-close financial test and four Compose regressions, without exposing secrets."""
import argparse,json,pathlib,re,shlex,subprocess
p=argparse.ArgumentParser();p.add_argument('--config',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--adb',default='adb');a=p.parse_args()
cfg=json.loads(a.config.read_text())
if set(cfg)!={'venue','operator','testPin'} or not cfg['venue'].startswith('spec033-'):raise SystemExit('Dedicated private synthetic fixture required')
if any(not isinstance(v,str) or not re.fullmatch(r'[A-Za-z0-9_-]+',v) for v in cfg.values()):raise SystemExit('Unsafe runner fixture argument')
a.output.mkdir(parents=True,exist_ok=True)
method='partialCashRemainsOpenAndFinalReceiptUsesCanonicalAutoClose'
for name,selected,count in [('live','LiveUx2ReceiptRecoveryTest#'+method,1),('ui','Ux2AccountPagesTest',4)]:
 cmd=[a.adb,'-s','emulator-5558','shell','am','instrument','-w','-r','-e','class','com.rodada.attendance.operations.'+selected]
 if name=='live':
  cmd+=['-e','liveUx2Receipt','true','-e','upstreamUrl','http://10.0.2.2:18139/']
  for k,v in cfg.items():cmd+=['-e',k,v]
 cmd+=['com.rodada.attendance.test/androidx.test.runner.AndroidJUnitRunner'];cmd=cmd[:4]+[shlex.join(cmd[4:])]
 try:r=subprocess.run(cmd,capture_output=True,text=True,timeout=300)
 except subprocess.TimeoutExpired:raise SystemExit('Instrumentation timed out; private arguments suppressed') from None
 out=r.stdout+r.stderr
 for v in cfg.values():out=out.replace(v,'[synthetic]')
 (a.output/(name+'.log')).write_text(out)
 statuses=re.findall(r'^INSTRUMENTATION_STATUS_CODE: (-?\d+)\s*$',out,re.M)
 if r.returncode or statuses!=['1','0']*count or not re.search(r'^INSTRUMENTATION_CODE: -1\s*$',out,re.M) or not re.search(r'^OK \('+str(count)+r' tests?\)\s*$',out,re.M):raise SystemExit('Failed '+name+'; inspect sanitized log')
 print('PASS: '+name+' '+str(count)+' executed tests; no skips.',flush=True)
