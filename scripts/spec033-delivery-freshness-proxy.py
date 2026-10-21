"""Loopback-only read fault proxy for isolated Spec033 native freshness tests."""
import http.client,json,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
state={'queue':False,'core':False,'hold':False,'held':False,'service':False};lock=threading.Lock();release=threading.Event()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):self.handle_request()
 def do_POST(self):self.handle_request()
 def handle_request(self):
  body=self.rfile.read(int(self.headers.get('Content-Length',0)))
  if self.path.startswith('/__freshness/'):
   with lock:
    if self.path.endswith('/arm'):
     state.update(json.loads(body));state['held']=False
     if state['hold']:release.clear()
     else:release.set()
    if self.path.endswith('/configure'):
     settings=json.loads(body);state.update(queue=settings['queue'],core=settings['core'],hold=settings['hold'],service=settings.get('service',False))
    if self.path.endswith('/release'):release.set()
    data=json.dumps(state).encode()
   self.reply(200,data);return
  with lock:queue_path='/dispatch/requests/' if state['service'] else '/dispatch/delivery/'
  queue=self.command=='GET' and self.path==queue_path
  with lock:fail=state['queue'] if queue else state['core'] and self.command=='GET' and self.path.startswith('/tabs/?');hold=queue and state['hold']
  if hold and not fail:
   conn=http.client.HTTPConnection('127.0.0.1',18134,timeout=20)
   headers={k:v for k,v in self.headers.items() if k.lower() not in ('host','connection','content-length')}
   conn.request(self.command,self.path,body,headers);res=conn.getresponse();held_data=res.read();held_status=res.status;conn.close()
  if hold:
   # Stream harmless JSON whitespace so the real client's read timeout stays
   # unchanged. Only explicit release completes the retained response.
   self.send_response(503 if fail else held_status);self.send_header('Content-Type','application/json');self.end_headers()
   with lock:state['held']=True
   try:
    while not release.wait(0.5):
     self.wfile.write(b' ');self.wfile.flush()
    data=b'{"code":"TEST_READ_UNAVAILABLE","message":"Synthetic read failure"}' if fail else held_data
    self.wfile.write(data)
   except (BrokenPipeError,ConnectionResetError):pass
   finally:
    with lock:state['held']=False
   return
  if fail:self.reply(503,b'{"code":"TEST_READ_UNAVAILABLE","message":"Synthetic read failure"}');return
  conn=http.client.HTTPConnection('127.0.0.1',18134,timeout=20)
  headers={k:v for k,v in self.headers.items() if k.lower() not in ('host','connection','content-length')}
  conn.request(self.command,self.path,body,headers);res=conn.getresponse();data=res.read();status=res.status;conn.close();self.reply(status,data)
 def reply(self,status,data):
  self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers()
  try:self.wfile.write(data)
  except (BrokenPipeError,ConnectionResetError):pass
ThreadingHTTPServer(('127.0.0.1',18136),Handler).serve_forever()
