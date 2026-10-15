"""Administrator provisioning only; no staff credentials or secret output."""

import argparse
import subprocess

from .windows_store import SERVICE_NAME, WindowsStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("configure",))
    parser.add_argument("--api-origin", required=True)
    parser.add_argument("--tcp-printer", action="append", default=None)
    args = parser.parse_args()
    subprocess.run(
        ["sc.exe", "config", SERVICE_NAME, "obj=", r"NT AUTHORITY\LocalService", "start=", "auto"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["sc.exe", "sidtype", SERVICE_NAME, "unrestricted"], check=True, capture_output=True
    )
    store = WindowsStore()
    store.provision(args.api_origin)
    if args.tcp_printer is not None:
        store.configure_tcp(args.tcp_printer)


if __name__ == "__main__":
    main()
