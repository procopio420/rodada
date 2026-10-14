"""Machine DPAPI state and protected service-SID ACLs; Windows-only adapter."""

import json
import os
import tempfile
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

from .worker import InstallationState

SERVICE_NAME = "RodadaImpressoras"
ROOT = Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "Rodada" / "Impressoras"


def windows_modules() -> tuple[Any, Any]:
    if os.name != "nt":
        raise OSError("Windows credential protection required.")
    import win32crypt
    import win32security

    return win32crypt, win32security


def service_sid() -> str:
    _, security = windows_modules()
    sid, _, _ = security.LookupAccountName(None, "NT SERVICE\\" + SERVICE_NAME)
    return str(security.ConvertSidToStringSid(sid))


def protect(path: Path, *, public: bool = False) -> None:
    _, security = windows_modules()
    sid = service_sid()
    dacl = f"D:P(A;OICI;RC;;;OW)(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FA;;;{sid})"
    if public:
        dacl += "(A;OICI;GR;;;BU)"
    descriptor = security.ConvertStringSecurityDescriptorToSecurityDescriptor(dacl, 1)
    security.SetFileSecurity(
        str(path),
        security.DACL_SECURITY_INFORMATION | security.PROTECTED_DACL_SECURITY_INFORMATION,
        descriptor,
    )


def atomic_write(path: Path, payload: bytes) -> None:
    descriptor, name = tempfile.mkstemp(prefix="state-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class WindowsStore:
    def __init__(self, root: Path = ROOT):
        self.root = root
        self.private = root / "private"
        self.public = root / "diagnostics"

    def provision(self, api_origin: str) -> None:
        from .client import validate_origin

        for existing in (self.root, *self.root.parents, self.private, self.public):
            if existing.is_symlink() or (os.name == "nt" and existing.is_junction()):
                raise OSError("Reparse point refused in service configuration path.")
        self.root.mkdir(parents=True, exist_ok=True)
        protect(self.root, public=True)
        for folder, public in ((self.private, False), (self.public, True)):
            folder.mkdir(exist_ok=True)
            protect(folder, public=public)
        atomic_write(
            self.private / "api.json", json.dumps({"origin": validate_origin(api_origin)}).encode()
        )
        if not (self.private / "state.dpapi").exists():
            self.save(InstallationState())

    def api_origin(self) -> str:
        data = json.loads((self.private / "api.json").read_text())
        return str(data["origin"])

    def load(self) -> InstallationState:
        crypto, _ = windows_modules()
        path = self.private / "state.dpapi"
        if not path.exists():
            return InstallationState()
        _, raw = crypto.CryptUnprotectData(path.read_bytes(), None, None, None, 1)
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise TypeError("Invalid protected state.")
        return InstallationState(**data)

    def save(self, state: InstallationState) -> None:
        crypto, _ = windows_modules()
        raw = json.dumps(asdict(state)).encode()
        encrypted = crypto.CryptProtectData(
            raw, "Rodada Impressoras", None, None, None, 4 | 1
        )  # LOCAL_MACHINE | UI_FORBIDDEN
        atomic_write(self.private / "state.dpapi", encrypted)

    def diagnostic(self, data: dict[str, str]) -> None:
        import win32ts

        allowed = ("state", "code", "expires_at", "version")
        safe = {key: data[key] for key in allowed if key in data}
        session_id = cast(Callable[[int], int], win32ts.ProcessIdToSessionId)
        safe["service_session"] = str(session_id(os.getpid()))
        atomic_write(self.public / "status.json", json.dumps(safe).encode())
