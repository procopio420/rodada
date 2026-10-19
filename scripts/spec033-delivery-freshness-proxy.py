"""Loopback-only read fault proxy for isolated Spec033 native freshness tests."""
import http.client,json,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
state={'queue':False,'core':False,'hold':False,'held':False};lock=threading.Lock();release=threading.Event()
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
     settings=json.loads(body);state.update(queue=settings['queue'],core=settings['core'],hold=settings['hold'])
    if self.path.endswith('/release'):release.set()
    data=json.dumps(state).encode()
   self.reply(200,data);return
  queue=self.command=='GET' and self.path=='/dispatch/delivery/'
  with lock:fail=state['queue'] if queue else state['core'] and self.command=='GET' and self.path.startswith('/tabs/?');hold=queue and state['hold']
  if hold:
   with lock:state['held']=True
   release.wait(20)
  if fail:self.reply(503,b'{"code":"TEST_READ_UNAVAILABLE","message":"Synthetic read failure"}');return
  conn=http.client.HTTPConnection('127.0.0.1',18134,timeout=20)
  headers={k:v for k,v in self.headers.items() if k.lower() not in ('host','connection','content-length')}
  conn.request(self.command,self.path,body,headers);res=conn.getresponse();data=res.read();status=res.status;conn.close();self.reply(status,data)
 def reply(self,status,data):
  self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers()
  try:self.wfile.write(data)
  except (BrokenPipeError,ConnectionResetError):pass
ThreadingHTTPServer(('127.0.0.1',18136),Handler).serve_forever()
