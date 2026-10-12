import sys,json,tempfile,socket,threading,os
from pathlib import Path
sys.path.insert(0,'/home/lucas/projects/rodada/pilot-pinned/apps/api')
from modules.documents_printing.adapters import FileAdapter,NetworkAdapter,SpoolAdapter
root=Path('/home/lucas/projects/rodada/pilot-artifacts');payload=b'\x1b@Rodada TEST ONLY\nCafe e acucar\n\x1dV\x00';received=[]
with tempfile.TemporaryDirectory(dir=root) as temporary:
 p=Path(temporary);file_result=FileAdapter(p/'file').deliver('test-final19',b'<html>TEST ONLY</html>');assert file_result.outcome=='OUTPUT_READY';assert (p/'file/test-final19.html').read_bytes()==b'<html>TEST ONLY</html>'
 sock=socket.socket();sock.bind(('127.0.0.1',0));sock.listen(1);port=sock.getsockname()[1]
 def accept():
  with sock:
   connection,_=sock.accept()
   with connection:
    data=b''
    while chunk:=connection.recv(4096):data+=chunk
    received.append(data)
 thread=threading.Thread(target=accept);thread.start();result=NetworkAdapter('127.0.0.1',port).deliver('test-final19',payload);thread.join(timeout=5);assert result.outcome=='SPOOL_ACCEPTED' and received==[payload]
 failed=NetworkAdapter('127.0.0.1',port).deliver('test-failed',payload);assert failed.outcome=='FAILED_RETRYABLE'
 executable=p/'lp-test';capture=p/'capture.json';executable.write_text('#!/usr/bin/env python3\nimport json,sys\nfrom pathlib import Path\nPath('+repr(str(capture))+').write_text(json.dumps({"args":sys.argv[1:],"payload":sys.stdin.buffer.read().hex()}))\n');executable.chmod(0o700)
 spool=SpoolAdapter('TEST_ONLY',str(executable)).deliver('test-final19',payload);data=json.loads(capture.read_text());assert spool.outcome=='SPOOL_ACCEPTED' and data['args']==['-d','TEST_ONLY','-o','raw','-t','Rodada-test-final19'] and data['payload']==payload.hex()
 evidence={'source_sha':'19dfc80e27f619a32c02518fad745e30db09830e','file':{'outcome':file_result.outcome,'exact_payload':True},'loopback_network':{'outcome':result.outcome,'bytes_received':len(payload),'exact_payload':True,'closed_port_outcome':failed.outcome},'cups_process_boundary':{'outcome':spool.outcome,'exact_argv_payload':True,'real_cups_queue_tested':False},'paper_tested':False,'physical_lan_tested':False,'scope':'Actual FILE/socket/subprocess boundaries using synthetic test ticket and local fake lp executable; no physical hardware'}
 Path('/tmp/rodada-pilot-final-evidence/print-transports.json').write_text(json.dumps(evidence,indent=2));print(json.dumps(evidence))
