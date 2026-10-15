"""Real noninteractive service/DPAPI/ACL gate on an isolated Windows runner."""

import json
import secrets
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import win32net
import win32netcon
import win32security
import win32service
import win32serviceutil

from rodada_printer_agent.windows_store import ROOT, SERVICE_NAME, WindowsStore, secure_directory


def wait_for(predicate, seconds=40):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.25)
    raise AssertionError("Windows service gate timed out")


def run(*arguments):
    result = subprocess.run(
        [sys.executable, *arguments], capture_output=True, text=True, timeout=60, check=False
    )
    if result.returncode:
        # CLI commands contain no secrets; source never prints protected state.
        raise AssertionError(result.stdout + result.stderr)


class Handler(BaseHTTPRequestHandler):
    response_status = 503
    calls = 0
    discovered = False

    def do_POST(self):
        Handler.calls += 1
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        self.send_response(Handler.response_status)
        self.end_headers()
        if Handler.response_status == 200:
            if self.path.endswith("/discovery/"):
                assert isinstance(body["printers"], list)
                assert all(row["health"] == "UNKNOWN" for row in body["printers"])
                Handler.discovered = True
                payload = {"protocol_version": 1, "observed": len(body["printers"])}
            else:
                payload = {"protocol_version": 1, "delivery_enabled": False}
            self.wfile.write(json.dumps(payload).encode())

    def log_message(self, *arguments):
        pass


def main():
    assert sys.platform == "win32", "Must run on real Windows"
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    username = "RodadaAclTest"
    user_created = False
    installed = False
    try:
        run("-m", "rodada_printer_agent.service", "--startup", "auto", "install")
        installed = True
        run(
            "-m",
            "rodada_printer_agent",
            "configure",
            "--api-origin",
            f"http://127.0.0.1:{server.server_port}",
        )
        # A precreated writable parent must fail closed rather than be repaired:
        # changing its ACL cannot revoke privileged handles already held by attackers.
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary) / "Rodada"
            parent.mkdir()
            unsafe = win32security.ConvertStringSecurityDescriptorToSecurityDescriptor(
                "D:P(A;OICI;FA;;;WD)", 1
            )
            win32security.SetFileSecurity(
                str(parent), win32security.DACL_SECURITY_INFORMATION, unsafe
            )
            try:
                WindowsStore(parent / "Impressoras").provision(
                    f"http://127.0.0.1:{server.server_port}"
                )
            except OSError:
                pass
            else:
                raise AssertionError("Unsafe precreated parent accepted")
        with tempfile.TemporaryDirectory() as temporary:
            unsafe_store = WindowsStore(Path(temporary) / "Rodada" / "Impressoras")
            secure_directory(unsafe_store.root.parent, public=True)
            secure_directory(unsafe_store.root, public=True)
            unsafe_store.private.mkdir()  # Inherits public BU read: never acceptable for secrets.
            try:
                unsafe_store.provision(f"http://127.0.0.1:{server.server_port}")
            except OSError:
                pass
            else:
                raise AssertionError("Readable precreated private directory accepted")
        with tempfile.TemporaryDirectory() as temporary:
            unsafe_store = WindowsStore(Path(temporary) / "Rodada" / "Impressoras")
            origin = f"http://127.0.0.1:{server.server_port}"
            unsafe_store.provision(origin)
            readable = win32security.ConvertStringSecurityDescriptorToSecurityDescriptor(
                "D:P(A;;FA;;;BA)(A;;GR;;;BU)", 1
            )
            win32security.SetFileSecurity(
                str(unsafe_store.private / "state.dpapi"),
                win32security.DACL_SECURITY_INFORMATION,
                readable,
            )
            try:
                unsafe_store.provision(origin)
            except OSError:
                pass
            else:
                raise AssertionError("Readable retained credential file accepted")
        store = WindowsStore()
        state = store.load()
        installation_id = state.installation_id
        state.credential = "rpa_" + secrets.token_urlsafe(32)
        state.activated = True
        store.save(state)
        assert store.load().credential == state.credential
        assert state.credential.encode() not in (store.private / "state.dpapi").read_bytes()
        password = secrets.token_urlsafe(32) + "Aa1!"
        win32net.NetUserAdd(
            None,
            1,
            {
                "name": username,
                "password": password,
                "priv": win32netcon.USER_PRIV_USER,
                "home_dir": "",
                "comment": "Disposable ACL test",
                "flags": win32netcon.UF_SCRIPT | win32netcon.UF_DONT_EXPIRE_PASSWD,
                "script_path": "",
            },
        )
        user_created = True
        token = win32security.LogonUser(
            username,
            ".",
            password,
            win32security.LOGON32_LOGON_INTERACTIVE,
            win32security.LOGON32_PROVIDER_DEFAULT,
        )
        try:
            win32security.ImpersonateLoggedOnUser(token)
            try:
                (store.private / "state.dpapi").read_bytes()
            except PermissionError:
                pass
            else:
                raise AssertionError("Unprivileged user can read DPAPI state")
            try:
                ROOT.rename(ROOT.with_name("StolenNamespace"))
            except PermissionError:
                pass
            else:
                raise AssertionError("Unprivileged user can replace service namespace")
        finally:
            win32security.RevertToSelf()
            token.Close()
        if win32serviceutil.QueryServiceStatus("Spooler")[1] != win32service.SERVICE_RUNNING:
            win32serviceutil.StartService("Spooler")
        win32serviceutil.StartService(SERVICE_NAME)
        wait_for(
            lambda: (
                win32serviceutil.QueryServiceStatus(SERVICE_NAME)[1] == win32service.SERVICE_RUNNING
            )
        )
        wait_for(lambda: Handler.calls > 0 and (ROOT / "diagnostics/status.json").exists())
        diagnostic = json.loads((ROOT / "diagnostics/status.json").read_text())
        assert diagnostic["service_session"] == "0", "Service must run without interactive desktop"
        assert state.credential not in json.dumps(diagnostic)
        assert state.proof not in json.dumps(diagnostic)
        manager = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
        handle = win32service.OpenService(manager, SERVICE_NAME, win32service.SERVICE_QUERY_CONFIG)
        try:
            service_config = win32service.QueryServiceConfig(handle)
        finally:
            win32service.CloseServiceHandle(handle)
            win32service.CloseServiceHandle(manager)
        assert service_config[1] == win32service.SERVICE_AUTO_START
        assert service_config[7].lower().endswith("localservice")
        Handler.response_status = 200
        wait_for(lambda: Handler.discovered)
        wait_for(
            lambda: json.loads((ROOT / "diagnostics/status.json").read_text())["state"] == "ONLINE"
        )
        win32serviceutil.StopService(SERVICE_NAME)
        wait_for(
            lambda: (
                win32serviceutil.QueryServiceStatus(SERVICE_NAME)[1] == win32service.SERVICE_STOPPED
            )
        )
        assert store.load().installation_id == installation_id
        run(
            "-m",
            "rodada_printer_agent",
            "configure",
            "--api-origin",
            f"http://127.0.0.1:{server.server_port}",
        )
        assert store.load().installation_id == installation_id
        assert store.load().credential == state.credential
        Handler.response_status = 401
        win32serviceutil.StartService(SERVICE_NAME)
        wait_for(lambda: store.load().authorization_lost)
        assert store.load().credential == ""
        print(
            "PASS: real DPAPI, service-SID ACL, LocalService/session0, autostart config, restart and revocation"
        )
    finally:
        if installed:
            if win32serviceutil.QueryServiceStatus(SERVICE_NAME)[1] != win32service.SERVICE_STOPPED:
                win32serviceutil.StopService(SERVICE_NAME)
                wait_for(
                    lambda: (
                        win32serviceutil.QueryServiceStatus(SERVICE_NAME)[1]
                        == win32service.SERVICE_STOPPED
                    )
                )
            win32serviceutil.RemoveService(SERVICE_NAME)
        if user_created:
            win32net.NetUserDel(None, username)
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == "__main__":
    main()
