"""Actual unsigned setup/reinstall/uninstall in an ephemeral Windows VM."""

import json
import subprocess
import sys
import time
from pathlib import Path

import win32service
import win32serviceutil

from rodada_printer_agent.windows_store import ROOT, SERVICE_NAME, WindowsStore


def run(*args):
    subprocess.run(args, check=True, timeout=180, capture_output=True)


def wait_service():
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        if win32serviceutil.QueryServiceStatus(SERVICE_NAME)[1] == win32service.SERVICE_RUNNING:
            return
        time.sleep(0.25)
    raise AssertionError("Packaged service did not start")


def main():
    assert sys.platform == "win32"
    installer = Path(sys.argv[1]).resolve()
    app = Path(r"C:\Program Files\Rodada\Impressoras")
    # Prior source smoke retained a revoked synthetic identity. Retain it: upgrades
    # must never silently replace identity or erase an interrupted result journal.
    before = WindowsStore().load()
    (ROOT / "diagnostics/status.json").unlink(missing_ok=True)
    run(str(installer), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-")
    wait_service()
    state = WindowsStore().load()
    assert state.installation_id == before.installation_id
    assert state.pending_result == before.pending_result
    run(str(app / "rodada-impressoras.exe"), "quiesce")
    # Reinstall exercises update/repair and binary replacement with service stopped.
    run(str(installer), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-")
    wait_service()
    assert WindowsStore().load().installation_id == before.installation_id
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if (ROOT / "diagnostics/status.json").exists():
            diagnostic = json.loads((ROOT / "diagnostics/status.json").read_text())
            if diagnostic.get("service_session") == "0" and diagnostic.get("version") == "0.5.0":
                break
        time.sleep(0.25)
    else:
        raise AssertionError("Missing session-0 packaged diagnostic")
    run(str(app / "unins000.exe"), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART")
    assert not (app / "rodada-impressoras.exe").exists()
    assert WindowsStore().load().installation_id == before.installation_id
    print("PASS: unsigned bundled installer, session 0, reinstall identity, uninstall retention")


if __name__ == "__main__":
    main()
