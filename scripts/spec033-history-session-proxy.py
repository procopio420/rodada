"""Loopback-only read latch for real ViewModel history session-generation tests."""
import http.client
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
lock = threading.Lock()
state = {'capture':'', 'mode':'success', 'heldOld':False, 'heldCurrent':False, 'historyReads':0}
events = {'old':threading.Event(), 'current':threading.Event()}
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*_): pass
    def do_GET(self): self.dispatch()
    def do_POST(self): self.dispatch()
    def dispatch(self):
        body = self.rfile.read(int(self.headers.get('Content-Length',0)))
        if self.path.startswith('/__history_fence/'):
            action = self.path.rsplit('/',1)[-1]
            with lock:
                if action == 'arm':
                    state.update(json.loads(body));state.update(capture='old',heldOld=False,heldCurrent=False,historyReads=0)
                    for event in events.values(): event.clear()
                if action == 'captureCurrent': state['capture']='current'
                if action == 'releaseOld': events['old'].set()
                if action == 'releaseCurrent': events['current'].set()
                data = json.dumps(state).encode()
            self.respond(200,data);return
        with lock:
            slot = state['capture'] if self.command == 'GET' and self.path == '/tabs/?active=false&offset=0' else ''
            if slot: state['capture']='';state['historyReads']+=1
            mode=state['mode']
        connection=http.client.HTTPConnection('127.0.0.1',18134,timeout=30)
        headers={k:v for k,v in self.headers.items() if k.lower() not in ('host','connection','content-length')}
        connection.request(self.command,self.path,body,headers)
        response=connection.getresponse();data=response.read();status=response.status;connection.close()
        if slot:
            if slot=='old' and mode=='failure': status=503;data=b'{"code":"SYNTHETIC_HISTORY_FAILURE"}'
            self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Connection','close');self.end_headers();self.close_connection=True
            with lock: state['held'+slot.capitalize()]=True
            try:
                for _ in range(360):
                    self.wfile.write(b' ');self.wfile.flush()
                    if events[slot].wait(0.25): break
                else:return
                self.wfile.write(data);self.wfile.flush()
            except (BrokenPipeError,ConnectionResetError): pass
            return
        self.respond(status,data)
    def respond(self,status,data):
        self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers()
        try:self.wfile.write(data)
        except (BrokenPipeError,ConnectionResetError):pass
if __name__=='__main__':ThreadingHTTPServer(('127.0.0.1',18140),Handler).serve_forever()
