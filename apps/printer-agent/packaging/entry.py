"""Frozen executable: service dispatcher, provisioning CLI or optional status UI."""

import sys

import pywintypes
import servicemanager
import win32service
import win32serviceutil

from rodada_printer_agent.service import PrinterService


def main():
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(PrinterService)
        servicemanager.StartServiceCtrlDispatcher()
    elif sys.argv[1] == "status":
        from rodada_printer_agent.ui import main as ui

        ui()
    elif sys.argv[1] == "configure":
        from rodada_printer_agent.__main__ import main as configure

        configure()
    elif sys.argv[1] == "quiesce":
        try:
            if win32serviceutil.QueryServiceStatus(PrinterService._svc_name_)[1] != win32service.SERVICE_STOPPED:
                win32serviceutil.StopService(PrinterService._svc_name_)
                win32serviceutil.WaitForServiceStatus(
                    PrinterService._svc_name_, win32service.SERVICE_STOPPED, 90
                )
        except pywintypes.error as error:
            if error.winerror != 1060:
                raise
    elif sys.argv[1] == "install-service":
        try:
            win32serviceutil.QueryServiceStatus(PrinterService._svc_name_)
            action = "update"
        except pywintypes.error as error:
            if error.winerror != 1060:
                raise
            action = "install"
        sys.argv = [sys.argv[0], "--startup", "auto", action]
        PrinterService._exe_name_ = sys.executable
        win32serviceutil.HandleCommandLine(
            PrinterService, serviceClassString="rodada_printer_agent.service.PrinterService"
        )
    elif sys.argv[1] == "service":
        del sys.argv[1]
        PrinterService._exe_name_ = sys.executable
        win32serviceutil.HandleCommandLine(
            PrinterService, serviceClassString="rodada_printer_agent.service.PrinterService"
        )
    else:
        raise SystemExit("Use status, configure or service.")


if __name__ == "__main__":
    main()
