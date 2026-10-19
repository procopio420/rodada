"""Local synthetic-session test only: hold committed service callbacks independently."""
import http.client
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

lock = threading.Lock()
state = {'x': '', 'y': '', 'mode': 'success', 'posts': [], 'heldX': False, 'heldY': False}
release_x = threading.Event()
release_y = threading.Event()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def do_GET(self): self.dispatch()
    def do_POST(self): self.dispatch()
    def dispatch(self):
        body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        if self.path.startswith('/__session_fence/'):
            action = self.path.rsplit('/', 1)[-1]
            with lock:
                if action == 'arm':
                    state.update(json.loads(body)); state.update(posts=[], heldX=False, heldY=False)
                    release_x.clear(); release_y.clear()
                if action == 'releaseX': release_x.set()
                if action == 'releaseY': release_y.set()
                data = json.dumps(state).encode()
            self.respond(200, data, [('Content-Type', 'application/json')]); return
        with lock:
            target = next((name for name in ('x','y') if self.command == 'POST' and self.path == f"/dispatch/requests/{state[name]}/claim/"), None)
            if target: state['posts'].append(state[target])
            mode = state['mode']
        connection = http.client.HTTPConnection('127.0.0.1', 18134, timeout=30)
        headers = {k:v for k,v in self.headers.items() if k.lower() not in ('host','connection','content-length')}
        connection.request(self.command, self.path, body, headers)
        response = connection.getresponse(); data = response.read(); status = response.status
        response_headers = response.getheaders(); connection.close()
        if target:
            if target == 'x' and mode == 'failure':
                status = 503; data = b'{"code":"SYNTHETIC_ACK_FAILURE","message":"Synthetic committed response lost"}'
            self.send_response(status)
            self.send_header('Content-Type','application/json')
            self.send_header('Connection','close'); self.end_headers()
            self.close_connection = True
            with lock: state['held' + target.upper()] = True
            # Whitespace is valid JSON framing and prevents the client's per-read timeout
            # from racing the intentional latch. No production timeout is changed.
            event = release_x if target == 'x' else release_y
            try:
                for _ in range(360):
                    self.wfile.write(b' '); self.wfile.flush()
                    if event.wait(0.25): break
                else: return
                self.wfile.write(data); self.wfile.flush()
            except (BrokenPipeError,ConnectionResetError): pass
            return
        self.respond(status, data, response_headers)
    def respond(self, status, data, headers):
        self.send_response(status)
        for key, value in headers:
            if key.lower() not in ('content-length','connection','transfer-encoding'): self.send_header(key,value)
        self.send_header('Content-Length', str(len(data))); self.end_headers()
        try: self.wfile.write(data)
        except (BrokenPipeError,ConnectionResetError): pass

if __name__ == '__main__': ThreadingHTTPServer(('127.0.0.1',18137),Handler).serve_forever()
