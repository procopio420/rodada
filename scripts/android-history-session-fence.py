"""Execute exactly one opt-in real session-fence test, rejecting assumption skips."""
import json
import pathlib
import re
import subprocess
import shlex
import sys

allowed = {'venue','operator','testPin','operatorB','testPinB','liveHistorySessionFence'}
config = json.loads(pathlib.Path(sys.argv[1]).read_text())
if set(config) != allowed or config['liveHistorySessionFence'] != 'true':
    raise SystemExit('Invalid private session fixture config')
for key, value in config.items():
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_.,:{}"\[\]-]+',value):
        raise SystemExit('Unsafe instrumentation fixture argument')
method = 'lateHistorySuccessAndFailureCannotFinishNewHistoryAcrossSessionGenerations'
command = ['adb','-s','emulator-5558','shell','am','instrument','-w','-r','-e','class',
           'com.rodada.attendance.operations.LiveHistorySessionFenceTest#'+method]
for key, value in config.items(): command += ['-e',key,value]
command += ['com.rodada.attendance.test/androidx.test.runner.AndroidJUnitRunner']
command = command[:4] + [shlex.join(command[4:])]
try:
    result = subprocess.run(command,capture_output=True,text=True,timeout=300)
except subprocess.TimeoutExpired:
    raise SystemExit("Instrumentation timed out; private runner arguments suppressed") from None
transcript = result.stdout+'\n'+result.stderr
for key in ('testPin','testPinB'): transcript = transcript.replace(config[key],'<synthetic-pin-redacted>')
path = pathlib.Path(sys.argv[2]); path.write_text(transcript)
statuses = re.findall(r'^INSTRUMENTATION_STATUS_CODE: (-?\d+)\s*$',transcript,re.M)
methods = re.findall(r'^INSTRUMENTATION_STATUS: test=(\S+)\s*$',transcript,re.M)
if result.returncode != 0 or statuses != ['1','0'] or methods != [method,method] or not re.search(r'^INSTRUMENTATION_CODE: -1\s*$',transcript,re.M):
    raise SystemExit('Real ViewModel session fence test did not execute and pass; inspect sanitized transcript')
print('PASS: one real ViewModel method, four history success/failure and A/B/A session cases; no skips.')
