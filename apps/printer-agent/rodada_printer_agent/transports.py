"""Bounded local transports. Success means accepted, never physical paper."""

import base64
import hashlib
import ipaddress
import socket
import time
from collections.abc import Callable
from contextlib import suppress
from typing import Any, Protocol, cast

from .contracts import SubmissionOutcome, SubmissionResult


class FontSettings(Protocol):
    lfFaceName: str
    lfHeight: int


class WindowsBackend(Protocol):
    def enumerate(self) -> list[dict[str, str]]: ...
    def raw(self, queue: str, content: bytes, *, deadline: float) -> str: ...
    def rendered(self, queue: str, text: str, columns: int, *, deadline: float) -> str: ...


def private_address(value: str, port: int) -> str:
    address = ipaddress.ip_address(value)
    networks = ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "fc00::/7")
    if port != 9100 or not any(address in ipaddress.ip_network(n) for n in networks):
        raise ValueError("Private literal printer address required on port9100.")
    return str(address)


class Transports:
    def __init__(self, windows: WindowsBackend, tcp_targets: tuple[str, ...] = ()):
        self.windows, self.tcp_targets = windows, tcp_targets

    def inventory(self) -> list[dict[str, str]]:
        printers = self.windows.enumerate()
        for address in self.tcp_targets:
            value = private_address(address, 9100)
            printers.append(
                {
                    "local_id": "tcp:" + value,
                    "label": "LAN " + value,
                    "queue_name": value,
                    "transport": "TCP_LAN",
                    "driver_name": "",
                    "health": "UNKNOWN",
                }
            )
        if len(printers) > 100:
            raise ValueError("Inventory exceeds100printers.")
        return printers

    def prepare(self, job: dict[str, Any]) -> bytes:
        if job["width_mm"] not in (58, 80):
            raise ValueError("Unsupported width.")
        content = base64.b64decode(job["content"], validate=True)
        if len(content) > 262144 or hashlib.sha256(content).hexdigest() != job["sha256"]:
            raise ValueError("Invalid document payload.")
        transport, profile = job["transport"], job["profile_id"]
        if transport == "WINDOWS_DRIVER" and profile == "windows-driver-v1":
            text = content.decode("utf-8")
            if any(ord(c) < 32 and c != "\n" for c in text):
                raise ValueError("Unexpected rendered control.")
        elif (
            transport in ("WINDOWS_RAW", "TCP_LAN")
            and profile in ("escpos-ascii-v1", "escpos-pc860-v1", "escpos-pc860-cut-v1")
            and job.get("raw_escpos_verified") is True
        ):
            prefix = b"\x1b@" if profile == "escpos-ascii-v1" else b"\x1b@\x1bt\x03"
            suffix = b"\x1dV\x00" if profile == "escpos-pc860-cut-v1" else b""
            if not content.startswith(prefix) or (suffix and not content.endswith(suffix)):
                raise ValueError("Invalid profile command envelope.")
            body = content[len(prefix):len(content) - len(suffix) if suffix else None]
            if any(c < 32 and c != 10 or c == 127 for c in body):
                raise ValueError("Unexpected RAW controls.")
            if profile == "escpos-ascii-v1" and any(c > 127 for c in body):
                raise ValueError("ASCII profile requires explicit transliteration.")
        else:
            raise ValueError("Driver/transport/compatibility mismatch.")
        if transport == "TCP_LAN":
            private_address(job["destination"], job["port"])
        elif not job["destination"] or any(ord(c) < 32 for c in job["destination"]):
            raise ValueError("Invalid Windows queue.")
        return content

    def submit(self, job: dict[str, Any], content: bytes, *, deadline: float) -> SubmissionResult:
        if time.monotonic() >= deadline:
            return SubmissionResult(SubmissionOutcome.DELIVERY_UNCERTAIN)
        if job["transport"] == "TCP_LAN":
            address = private_address(job["destination"], job["port"])
            # A failed connect is provably before sending application bytes.
            try:
                connection = socket.create_connection((address, job["port"]), timeout=5)
            except OSError:
                return SubmissionResult(SubmissionOutcome.FAILED_RETRYABLE)
            try:
                with connection:
                    connection.settimeout(5)
                    if time.monotonic() >= deadline:
                        return SubmissionResult(SubmissionOutcome.DELIVERY_UNCERTAIN)
                    connection.sendall(content)
                return SubmissionResult(SubmissionOutcome.SPOOL_ACCEPTED)
            except OSError:
                return SubmissionResult(SubmissionOutcome.DELIVERY_UNCERTAIN)
        # Even an exception in StartDoc/EndDoc may have side effects. No automatic retry.
        try:
            if job["transport"] == "WINDOWS_RAW":
                spool_id = self.windows.raw(job["destination"], content, deadline=deadline)
            else:
                spool_id = self.windows.rendered(
                    job["destination"],
                    content.decode("utf-8"),
                    32 if job["width_mm"] == 58 else 48,
                    deadline=deadline,
                )
            return SubmissionResult(SubmissionOutcome.SPOOL_ACCEPTED, spool_id)
        except Exception:  # noqa: BLE001 -- opaque driver failures cannot prove no submission
            return SubmissionResult(SubmissionOutcome.DELIVERY_UNCERTAIN)


class NativeWindows:
    """APIs run under the service identity, not an interactive user's printer list."""

    def enumerate(self) -> list[dict[str, str]]:
        import win32print

        result = []
        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        for printer in win32print.EnumPrinters(flags, None, 2):
            queue = str(printer["pPrinterName"])
            result.append(
                {
                    "local_id": "queue:" + hashlib.sha256(queue.encode()).hexdigest(),
                    "label": queue[:120],
                    "queue_name": queue,
                    "transport": "WINDOWS_DRIVER",
                    "driver_name": str(printer["pDriverName"])[:120],
                    "health": "UNKNOWN",
                }
            )
        return result

    def raw(self, queue: str, content: bytes, *, deadline: float) -> str:
        import win32print

        handle = win32print.OpenPrinter(queue)
        try:
            if time.monotonic() >= deadline:
                raise OSError("Attempt lease elapsed before spool entry.")
            spool_id = win32print.StartDocPrinter(
                handle, 1, ("Rodada - DOCUMENTO NAO FISCAL", None, "RAW")
            )
            win32print.StartPagePrinter(handle)
            if win32print.WritePrinter(handle, content) != len(content):
                raise OSError("Partial spool write.")
            win32print.EndPagePrinter(handle)
            win32print.EndDocPrinter(handle)
            return str(spool_id)
        except Exception:
            # Best effort cleanup cannot prove no paper; callers retain UNCERTAIN.
            with suppress(Exception):
                win32print.AbortPrinter(handle)
            raise
        finally:
            win32print.ClosePrinter(handle)

    def rendered(self, queue: str, text: str, columns: int, *, deadline: float) -> str:
        import win32con
        import win32gui
        import win32print

        dc = cast(Callable[[str, str, None], int], win32gui.CreateDC)("WINSPOOL", queue, None)
        font = None
        previous = None
        try:
            width = win32print.GetDeviceCaps(dc, win32con.HORZRES)
            height = win32print.GetDeviceCaps(dc, win32con.VERTRES)
            if width < 8 or height < 8:
                raise OSError("Invalid printable area.")
            line_height = max(
                8,
                min(
                    win32print.GetDeviceCaps(dc, win32con.LOGPIXELSY) * 10 // 72,
                    width * 2 // columns,
                ),
            )
            definition = win32gui.LOGFONT()
            # SDK supports writable LOGFONT fields; bundled stubs mark these read-only.
            settings = cast(FontSettings, definition)
            settings.lfFaceName = "Consolas"
            settings.lfHeight = -line_height
            font = win32gui.CreateFontIndirect(definition)
            previous = win32gui.SelectObject(dc, font)
            if time.monotonic() >= deadline:
                raise OSError("Attempt lease elapsed before rendered spool entry.")
            spool_id = win32print.StartDoc(dc, ("Rodada - DOCUMENTO NAO FISCAL", None, None, 0))
            win32print.StartPage(dc)
            y = 0
            for line in text.splitlines():
                parts = [line]
                while parts:
                    part = parts.pop(0)
                    if win32gui.GetTextExtentPoint32(dc, part)[0] > width:
                        split = len(part) - 1
                        while (
                            split > 1 and win32gui.GetTextExtentPoint32(dc, part[:split])[0] > width
                        ):
                            split -= 1
                        parts.insert(0, part[split:])
                        part = part[:split]
                    if y + line_height > height:
                        win32print.EndPage(dc)
                        win32print.StartPage(dc)
                        y = 0
                    cast(
                        Callable[[int, str, int, tuple[int, int, int, int], int], int],
                        win32gui.DrawText,
                    )(
                        dc,
                        part,
                        -1,
                        (0, y, width, y + line_height),
                        win32con.DT_LEFT | win32con.DT_NOPREFIX | win32con.DT_SINGLELINE,
                    )
                    y += line_height + 2
            win32print.EndPage(dc)
            win32print.EndDoc(dc)
            return str(spool_id)
        except Exception:
            with suppress(Exception):
                win32print.AbortDoc(dc)
            raise
        finally:
            if previous is not None:
                win32gui.SelectObject(dc, previous)
            if font is not None:
                win32gui.DeleteObject(font)
            win32gui.DeleteDC(dc)
