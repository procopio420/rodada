import base64
import hashlib
import time
from unittest.mock import MagicMock, patch

import pytest
from test_worker import Api, Store

from rodada_printer_agent.delivery import DeliveryCycle
from rodada_printer_agent.transports import Transports, private_address
from rodada_printer_agent.worker import Worker


def job(transport="WINDOWS_DRIVER"):
    raw = transport != "WINDOWS_DRIVER"
    content = b"\x1b@DOCUMENTO NAO FISCAL\n\n\n" if raw else "DOCUMENTO NÃO FISCAL\n".encode()
    return {
        "job_id": "12345678-1234-1234-1234-123456789012",
        "attempt_token": "token",
        "route_id": "route",
        "route_version": 1,
        "lease_seconds": 55,
        "width_mm": 80,
        "destination": "192.168.1.50" if transport == "TCP_LAN" else "Synthetic queue",
        "port": 9100,
        "transport": transport,
        "profile_id": "escpos-ascii-v1" if raw else "windows-driver-v1",
        "raw_escpos_verified": raw,
        "content": base64.b64encode(content).decode(),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


@pytest.mark.parametrize("transport", ["WINDOWS_DRIVER", "WINDOWS_RAW"])
def test_spool_acceptance_never_means_paper_and_modes_are_separate(transport):
    windows = MagicMock()
    windows.raw.return_value = windows.rendered.return_value = "42"
    delivery = Transports(windows)
    task = job(transport)
    result = delivery.submit(task, delivery.prepare(task), deadline=time.monotonic() + 55)
    assert result.outcome == "SPOOL_ACCEPTED" and result.spool_id == "42"
    assert windows.raw.call_count == (transport == "WINDOWS_RAW")
    assert windows.rendered.call_count == (transport == "WINDOWS_DRIVER")
    windows.raw.side_effect = windows.rendered.side_effect = OSError("Synthetic driver failure")
    assert (
        delivery.submit(task, delivery.prepare(task), deadline=time.monotonic() + 55).outcome
        == "DELIVERY_UNCERTAIN"
    )


def test_raw_requires_attestation_and_payload_hash_and_no_cut():
    delivery = Transports(MagicMock())
    task = job("WINDOWS_RAW")
    task["raw_escpos_verified"] = False
    with pytest.raises(ValueError):
        delivery.prepare(task)
    task["raw_escpos_verified"] = True
    task["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        delivery.prepare(task)


@pytest.mark.parametrize(
    "value", ["8.8.8.8", "127.0.0.1", "169.254.169.254", "example.com", "::1", "::ffff:192.168.1.1"]
)
def test_tcp_no_dns_public_loopback_metadata_or_mapped_bypass(value):
    with pytest.raises(ValueError):
        private_address(value, 9100)


def test_tcp_connect_failure_vs_partial_write():
    delivery, task = Transports(MagicMock()), job("TCP_LAN")
    with patch("socket.create_connection", side_effect=OSError("Synthetic connect failure")):
        assert (
            delivery.submit(task, delivery.prepare(task), deadline=time.monotonic() + 55).outcome
            == "FAILED_RETRYABLE"
        )
    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.sendall.side_effect = OSError("Synthetic partial write")
    with patch("socket.create_connection", return_value=connection):
        assert (
            delivery.submit(task, delivery.prepare(task), deadline=time.monotonic() + 55).outcome
            == "DELIVERY_UNCERTAIN"
        )


def test_lost_result_ack_restart_reconciles_without_second_submission():
    store, api, windows = Store(), Api(), MagicMock()
    api.approved = True
    windows.enumerate.return_value = []
    original = api.post
    calls, claimed = [], False

    def post(path, body, token=""):
        nonlocal claimed
        calls.append((path, body))
        if path == "me/heartbeat/":
            return {"protocol_version": 1, "delivery_enabled": True}
        if path == "me/discovery/":
            return {"observed": 0}
        if path == "me/claim/":
            result = None if claimed else job()
            claimed = True
            return {"job": result}
        if path.endswith("/result/"):
            if len([p for p, _ in calls if p.endswith("/result/")]) == 1:
                raise OSError("Synthetic lost ACK")
            return {"accepted": True}
        return original(path, body, token)

    api.post = post
    cycle = DeliveryCycle(Transports(windows))
    Worker(store, api, cycle).tick("Synthetic PC")
    assert store.state.pending_result["outcome"] == "SPOOL_ACCEPTED"
    Worker(store, api, cycle).tick("Synthetic PC")
    assert windows.rendered.call_count == 1 and store.state.pending_result == {}


def test_persisted_crash_marker_is_reported_uncertain_without_spool():
    store, api, windows = Store(), Api(), MagicMock()
    store.state.credential = api.raw
    store.state.activated = True
    store.state.pending_result = {
        key: value
        for key, value in job().items()
        if key in ("job_id", "attempt_token", "route_id", "route_version")
    }
    store.state.pending_result["outcome"] = "DELIVERY_UNCERTAIN"
    windows.enumerate.return_value = []
    original = api.post
    reported = []

    def post(path, body, token=""):
        if path.endswith("/result/"):
            reported.append(body)
            return {"accepted": True}
        if path == "me/discovery/":
            return {"observed": 0}
        return original(path, body, token)

    api.post = post
    Worker(store, api, DeliveryCycle(Transports(windows))).tick("Synthetic PC")
    assert reported[0]["outcome"] == "DELIVERY_UNCERTAIN"
    windows.raw.assert_not_called()
    windows.rendered.assert_not_called()


def test_native_apis_raw_vs_gdi_and_service_queue_enumeration(monkeypatch):
    import sys
    from types import SimpleNamespace

    from rodada_printer_agent.transports import NativeWindows

    spool, gui = MagicMock(), MagicMock()
    constants = SimpleNamespace(
        HORZRES=1, VERTRES=2, LOGPIXELSY=3, DT_LEFT=0, DT_NOPREFIX=2048, DT_SINGLELINE=32
    )
    spool.PRINTER_ENUM_LOCAL, spool.PRINTER_ENUM_CONNECTIONS = 2, 4
    spool.EnumPrinters.return_value = [
        {"pPrinterName": "Synthetic Queue", "pDriverName": "Synthetic Driver"}
    ]
    spool.StartDocPrinter.return_value = 41
    spool.StartDoc.return_value = 42
    spool.WritePrinter.side_effect = lambda handle, content: len(content)
    spool.GetDeviceCaps.side_effect = lambda dc, index: {1: 320, 2: 100, 3: 203}[index]
    (
        gui.CreateDC.return_value,
        gui.CreateFontIndirect.return_value,
        gui.SelectObject.return_value,
    ) = 1, 2, 3
    gui.LOGFONT.side_effect = lambda: SimpleNamespace(lfFaceName="", lfHeight=0)
    gui.GetTextExtentPoint32.side_effect = lambda dc, text: (len(text) * 6, 12)
    monkeypatch.setitem(sys.modules, "win32print", spool)
    monkeypatch.setitem(sys.modules, "win32gui", gui)
    monkeypatch.setitem(sys.modules, "win32con", constants)
    windows = NativeWindows()
    assert windows.enumerate()[0]["health"] == "UNKNOWN"
    spool.EnumPrinters.assert_called_once_with(6, None, 2)
    assert (
        windows.rendered(
            "Synthetic Queue",
            "DOCUMENTO NÃO FISCAL\n" + "X" * 70 + "\n" * 20,
            48,
            deadline=time.monotonic() + 55,
        )
        == "42"
    )
    spool.WritePrinter.assert_not_called()
    assert gui.DrawText.call_count > 2 and spool.StartPage.call_count > 1
    spool.StartDocPrinter.assert_not_called()
    assert (
        windows.raw("Synthetic Queue", b"\x1b@Synthetic\n", deadline=time.monotonic() + 55) == "41"
    )
    assert spool.StartDocPrinter.call_args.args[2][2] == "RAW"
    spool.WritePrinter.return_value = 0
    spool.WritePrinter.side_effect = None
    with pytest.raises(OSError):
        windows.raw("Synthetic Queue", b"partial", deadline=time.monotonic() + 55)
    assert spool.ClosePrinter.call_count == 2


@pytest.mark.parametrize("pause_at", ["claim", "prepare"])
def test_expired_claim_or_pause_before_submit_never_sends(pause_at, monkeypatch):
    now = [0.0]
    monkeypatch.setattr("time.monotonic", lambda: now[0])
    store, windows = Store(), MagicMock()
    windows.enumerate.return_value = []
    cycle = DeliveryCycle(Transports(windows))
    reported = []
    original = cycle.transports.prepare

    def prepare(task):
        content = original(task)
        if pause_at == "prepare":
            now[0] = 100.0
        return content

    monkeypatch.setattr(cycle.transports, "prepare", prepare)

    class Api:
        def post(self, path, body, token=""):
            if path == "me/claim/":
                if pause_at == "claim":
                    now[0] = 100.0
                return {"job": job()}
            if path.endswith("/result/"):
                reported.append(body)
                return {"accepted": False}
            return {"observed": 0}

    cycle.tick(Api(), store.state, store, True)
    windows.rendered.assert_not_called()
    windows.raw.assert_not_called()
    assert reported[0]["outcome"] == "DELIVERY_UNCERTAIN"


def test_tcp_connection_delay_past_deadline_sends_no_bytes(monkeypatch):
    now = [0.0]
    monkeypatch.setattr("time.monotonic", lambda: now[0])
    connection = MagicMock()
    connection.__enter__.return_value = connection

    def connect(*args, **kwargs):
        now[0] = 100.0
        return connection

    monkeypatch.setattr("socket.create_connection", connect)
    delivery, task = Transports(MagicMock()), job("TCP_LAN")
    assert (
        delivery.submit(task, delivery.prepare(task), deadline=55).outcome == "DELIVERY_UNCERTAIN"
    )
    connection.sendall.assert_not_called()
