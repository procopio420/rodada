"""Local fault harness: real upstream responses, no fabricated success."""
import json,time,http.client,threading,hashlib
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
control=Path(__file__).with_name('proxy-control.json')
class Handler(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def log_message(self,*args): pass
    def do_GET(self): self.forward()
    def do_POST(self): self.forward()
    def do_PATCH(self): self.forward()
    def forward(self):
        cfg=json.loads(control.read_text()) if control.exists() else {}
        match=cfg.get('match','') in self.path
        data=self.rfile.read(int(self.headers.get('Content-Length',0)))
        if self.command=='POST' and self.path.endswith('/orders/confirm/'):
            row={'path':self.path,'payload_sha256':hashlib.sha256(data).hexdigest(),'body':json.loads(data),'timestamp_machine':time.time(),'stage':'received'}
            with control.with_name('order-transport.jsonl').open('a') as f: f.write(json.dumps(row)+'\n')
        if match and cfg.get('delay'): time.sleep(cfg['delay'])
        if match and cfg.get('status'):
            body=json.dumps({'code':'AUDIT_CONTROLLED_FAILURE','detail':'Falha controlada no harness local de auditoria.'}).encode()
            self.send_response(cfg['status']); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body); return
        try:
            conn=http.client.HTTPConnection('127.0.0.1',18081,timeout=60)
            headers={k:v for k,v in self.headers.items() if k.lower() not in ['host','connection']}; headers['Host']='127.0.0.1:18081'
            conn.request(self.command,self.path,body=data,headers=headers)
            response=conn.getresponse()
            # Never buffer an infinite SSE stream; forward with chunked framing.
            if 'text/event-stream' in response.getheader('Content-Type',''):
                self.send_response(response.status); self.send_header('Content-Type','text/event-stream'); self.send_header('Transfer-Encoding','chunked'); self.end_headers()
                while True:
                    chunk=response.read1(4096)
                    if not chunk: break
                    self.wfile.write(f'{len(chunk):x}\r\n'.encode()+chunk+b'\r\n'); self.wfile.flush()
                self.wfile.write(b'0\r\n\r\n'); return
            body=response.read()
            if self.command=='POST' and self.path.endswith('/orders/confirm/'):
                with control.with_name('order-transport.jsonl').open('a') as f: f.write(json.dumps({'path':self.path,'payload_sha256':hashlib.sha256(data).hexdigest(),'status':response.status,'timestamp_machine':time.time(),'stage':'upstream_response'})+'\n')
            if match and cfg.get('after_delay'): time.sleep(cfg['after_delay'])
            if match and cfg.get('drop_after_commit'):
                self.close_connection=True; self.connection.shutdown(2); self.connection.close(); return
            self.send_response(response.status)
            for k,v in response.getheaders():
                if k.lower() not in ['content-length','connection','transfer-encoding']: self.send_header(k,v)
            self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError): pass
        except Exception:
            self.close_connection=True
ThreadingHTTPServer(('0.0.0.0',18080),Handler).serve_forever()
