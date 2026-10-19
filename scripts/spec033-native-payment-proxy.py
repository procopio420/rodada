"""Local emulator current-main test API proxy; records counts, never request bodies/auth."""
import http.client,json,re,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
counts={'payments':0,'close':0};lock=threading.Lock()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):self.forward()
 def do_POST(self):self.forward()
 def forward(self):
  body=self.rfile.read(int(self.headers.get('Content-Length',0)))
  if self.path=='/__autoclose/status':
   with lock:data=json.dumps(counts).encode()
   self.send_response(200);self.end_headers();self.wfile.write(data);return
  if self.command=='POST':
   with lock:
    if re.fullmatch(r'/tabs/[a-f0-9-]+/payments/',self.path):counts['payments']+=1
    if re.fullmatch(r'/tabs/[a-f0-9-]+/close/',self.path):counts['close']+=1
  connection=http.client.HTTPConnection('127.0.0.1',18138,timeout=30)
  headers={k:v for k,v in self.headers.items() if k.lower() not in ('host','connection','content-length')}
  try:
   connection.request(self.command,self.path,body,headers);response=connection.getresponse();data=response.read()
   self.send_response(response.status)
   for k,v in response.getheaders():
    if k.lower() not in ('transfer-encoding','connection','content-length'):self.send_header(k,v)
   self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  finally:connection.close()
ThreadingHTTPServer(('0.0.0.0',18139),Handler).serve_forever()
