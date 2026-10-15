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


def trusted_provisioning_sids(security: Any) -> set[str]:
    import win32api
    import win32con

    admins = security.CreateWellKnownSid(security.WinBuiltinAdministratorsSid)
    if not security.CheckTokenMembership(None, admins):
        raise OSError("Administrative provisioning required.")
    token = security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
    try:
        caller = security.GetTokenInformation(token, security.TokenUser)[0]
    finally:
        token.Close()
    return {"S-1-5-18", "S-1-5-32-544", service_sid(), security.ConvertSidToStringSid(caller)}


def validate_existing_acl(
    path: Path, security: Any, trusted: set[str], *, public: bool, service_file: bool = False
) -> None:
    existing = security.GetFileSecurity(
        str(path), security.OWNER_SECURITY_INFORMATION | security.DACL_SECURITY_INFORMATION
    )
    owner = security.ConvertSidToStringSid(existing.GetSecurityDescriptorOwner())
    if owner not in trusted and not (service_file and owner == "S-1-5-19"):
        raise OSError("Untrusted storage owner; administrative recovery required.")
    acl = existing.GetSecurityDescriptorDacl()
    if acl is None:
        raise OSError("Unprotected service storage.")
    dangerous = 0x40000000 | 0x10000000 | 0xD0156
    if not public:
        dangerous |= 0x80000000 | 0x1  # GENERIC_READ | FILE_READ_DATA
    owner_restricted = False
    for index in range(acl.GetAceCount()):
        ace = acl.GetAce(index)
        if ace[0][0] == security.ACCESS_ALLOWED_ACE_TYPE:
            principal = security.ConvertSidToStringSid(ace[2])
            if principal not in trusted and ace[1] & dangerous:
                raise OSError("Unsafe storage ACL; administrative recovery required.")
            if principal == "S-1-3-4":  # OWNER_RIGHTS removes implicit owner WRITE_DAC.
                owner_restricted = True
        elif ace[0][0] != security.ACCESS_DENIED_ACE_TYPE:
            raise OSError("Unsupported service storage ACL.")
    if owner == "S-1-5-19" and not owner_restricted:
        raise OSError("Shared LocalService ownership must restrict OWNER_RIGHTS.")


def secure_directory(path: Path, *, public: bool = False) -> None:
    """Create with its final ACL; never repair an untrusted namespace in place."""
    import pywintypes
    import win32file

    _, security = windows_modules()
    sid = service_sid()
    trusted = trusted_provisioning_sids(security)
    dacl = f"D:P(A;OICI;RC;;;OW)(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FA;;;{sid})"
    if public:
        dacl += "(A;OICI;GR;;;BU)"
    descriptor = security.ConvertStringSecurityDescriptorToSecurityDescriptor(dacl, 1)
    attributes = pywintypes.SECURITY_ATTRIBUTES()
    attributes.SECURITY_DESCRIPTOR = descriptor
    try:
        win32file.CreateDirectory(str(path), attributes)
    except pywintypes.error as error:
        if error.winerror != 183:  # ERROR_ALREADY_EXISTS
            raise
        if path.is_symlink() or path.is_junction() or not path.is_dir():
            raise OSError("Unsafe service directory.") from error
        validate_existing_acl(path, security, trusted, public=public)


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
        # Protect the dedicated parent before creating any service descendants.
        secure_directory(self.root.parent, public=True)
        secure_directory(self.root, public=True)
        for folder, public in ((self.private, False), (self.public, True)):
            secure_directory(folder, public=public)
        state_path = self.private / "state.dpapi"
        if state_path.exists() or state_path.is_symlink():
            if state_path.is_symlink() or state_path.is_junction() or not state_path.is_file():
                raise OSError("Unsafe retained credential path.")
            _, security = windows_modules()
            validate_existing_acl(
                state_path,
                security,
                trusted_provisioning_sids(security),
                public=False,
                service_file=True,
            )
        atomic_write(
            self.private / "api.json",
            json.dumps(
                {
                    "origin": validate_origin(api_origin),
                    "tcp_targets": self.tcp_targets()
                    if (self.private / "api.json").exists()
                    else [],
                }
            ).encode(),
        )
        if not (self.private / "state.dpapi").exists():
            self.save(InstallationState())

    def api_origin(self) -> str:
        data = json.loads((self.private / "api.json").read_text())
        return str(data["origin"])

    def tcp_targets(self) -> tuple[str, ...]:
        data = json.loads((self.private / "api.json").read_text())
        return tuple(str(value) for value in data.get("tcp_targets", []))

    def configure_tcp(self, targets: list[str]) -> None:
        from .transports import private_address

        if len(targets) > 20:
            raise ValueError("At most20manual LAN targets.")
        data = json.loads((self.private / "api.json").read_text())
        data["tcp_targets"] = [private_address(value, 9100) for value in targets]
        atomic_write(self.private / "api.json", json.dumps(data).encode())

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
