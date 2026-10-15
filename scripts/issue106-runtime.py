#!/usr/bin/env python3
"""Read-only runtime metadata for the exact disposable #106 stack."""
import json
import os
from pathlib import Path
import subprocess
import sys
from cross_surface_fixture import require_disposable_database, require_connected_database
require_disposable_database()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django
django.setup()
from django.db import connection
require_connected_database(connection)
with connection.cursor() as cursor:
    cursor.execute("SHOW server_version")
    postgresql = cursor.fetchone()[0]

def command(args, cwd=None):
    try:
        return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.DEVNULL, timeout=30).strip()
    except (OSError, subprocess.SubprocessError):
        return "NOT_AVAILABLE"

android = command(["adb", "shell", "getprop", "ro.build.version.sdk"])
if android == "NOT_AVAILABLE" and Path("artifacts/android-emulator-api.txt").exists():
    android = Path("artifacts/android-emulator-api.txt").read_text().strip()
node = command(["node", "--version"])
browser = command(["node", "-e", "const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();try{console.log(b.version())}finally{await b.close()}})().catch(()=>process.exit(1))"], "apps/web")
versions = {"sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "postgresql":postgresql,"django":django.get_version(),"android":"emulator API " + android,
    "browser":browser,"nextjs":command(["node","-p","require('next/package.json').version"],"apps/web"),
    "playwright":command(["node","-p","require('playwright/package.json').version"],"apps/web"),
    "python":sys.version.split()[0],"node":node}
Path(sys.argv[1]).write_text(json.dumps(versions,indent=2)+"\n")
