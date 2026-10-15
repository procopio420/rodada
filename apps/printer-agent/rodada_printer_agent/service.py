"""Development Windows service. Distribution/installer belong to S6."""

import socket
import threading
from typing import Any

import win32service
import win32serviceutil

from .client import AgentApi
from .windows_store import SERVICE_NAME, WindowsStore
from .worker import Worker


class PrinterService(win32serviceutil.ServiceFramework):
    _svc_name_ = SERVICE_NAME
    _svc_display_name_ = "Rodada Impressoras"
    _svc_description_ = "Integração local de impressoras Rodada."

    def __init__(self, args: Any):
        super().__init__(args)
        self.stop_event = threading.Event()

    def SvcStop(self) -> None:
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.stop_event.set()

    def SvcDoRun(self) -> None:
        store = WindowsStore()
        worker = Worker(store, AgentApi(store.api_origin()))
        while not self.stop_event.is_set():
            worker.tick(socket.gethostname()[:120])
            self.stop_event.wait(10)


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(
        PrinterService, serviceClassString="rodada_printer_agent.service.PrinterService"
    )
