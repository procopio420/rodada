"""Administrator provisioning only; no staff credentials or secret output."""

import argparse
import subprocess

from .windows_store import SERVICE_NAME, WindowsStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("configure",))
    parser.add_argument("--api-origin", required=True)
    args = parser.parse_args()
    subprocess.run(
        ["sc.exe", "config", SERVICE_NAME, "obj=", r"NT AUTHORITY\LocalService", "start=", "auto"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["sc.exe", "sidtype", SERVICE_NAME, "unrestricted"], check=True, capture_output=True
    )
    WindowsStore().provision(args.api_origin)


if __name__ == "__main__":
    main()
