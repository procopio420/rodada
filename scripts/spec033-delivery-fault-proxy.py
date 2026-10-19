"""Loopback-only fault proxy; never seeds or resets backend state."""
import http.client,json,socket,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit
lock=threading.Lock(); state={'mode':'off','task':'','posts':0,'held':False}; release=threading.Event()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def do_GET(self): self.handle_request()
 def do_POST(self): self.handle_request()
 def handle_request(self):
  body=self.rfile.read(int(self.headers.get('Content-Length',0)))
  if self.path.startswith('/__delivery_fault/'):
   action=self.path.rsplit('/',1)[-1]
   with lock:
    if action=='arm': state.update(json.loads(body));state.update(posts=0,held=False);release.clear()
    if action=='release': release.set()
    payload=json.dumps(state).encode()
   self.send_response(200);self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload);return
  with lock:
   mode=state['mode'];task=state['task'];completion=self.command=='POST' and self.path==f'/dispatch/delivery/{task}/complete/'
   if completion:state['posts']+=1
  conn=http.client.HTTPConnection('127.0.0.1',18134,timeout=15)
  headers={k:v for k,v in self.headers.items() if k.lower() not in ('host','connection','content-length')}
  conn.request(self.command,self.path,body,headers);res=conn.getresponse();data=res.read();status=res.status;response_headers=res.getheaders();conn.close()
  if completion and mode=='drop':
   self.connection.shutdown(socket.SHUT_RDWR);self.connection.close();return
  if self.command=='GET' and self.path=='/dispatch/delivery/' and mode.startswith('hold'):
   with lock:hold=state['posts']>0 and not state['held']
   if hold:
    with lock:state['held']=True
    release.wait(15)
    if mode=='hold-fail':status=503;data=b'{"code":"TEST_LATE_FAILURE","message":"Synthetic delayed test failure"}';response_headers=[('Content-Type','application/json')]
  self.send_response(status)
  for k,v in response_headers:
   if k.lower() not in ('content-length','connection','transfer-encoding'):self.send_header(k,v)
  self.send_header('Content-Length',str(len(data)));self.end_headers()
  try:self.wfile.write(data)
  except (BrokenPipeError,ConnectionResetError):pass
ThreadingHTTPServer(('127.0.0.1',18135),Handler).serve_forever()
