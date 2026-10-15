#!/usr/bin/env python3
"""Export redacted Playwright traces; preserve raw evidence locally, never upload it."""
import json
from pathlib import Path
import re
import zipfile

SENSITIVE = re.compile(r"^(?:pin|password|authorization|cookie|cookies|set-cookie|access_?token|refresh_?token|session_?token|csrf_?token|x-guest-session)$", re.I)
JWT = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")


def redact(value):
    if isinstance(value, dict):
        if SENSITIVE.fullmatch(str(value.get("name", ""))):
            return {**value, "value": "[REDACTED]"}
        return {k: "[REDACTED]" if SENSITIVE.fullmatch(k) else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        value = JWT.sub("[REDACTED_JWT]", value)
        # The only PIN used by this disposable harness. Includes fill() trace params/source.
        value = value.replace("2468", "[REDACTED_TEST_PIN]")
        try:
            nested = json.loads(value)
        except (ValueError, TypeError):
            return value
        if isinstance(nested, (dict, list)):
            return json.dumps(redact(nested), ensure_ascii=False)
        return value
    return value


def export(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as original, zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as output:
        for name in original.namelist():
            data = original.read(name)
            try:
                decoded = data.decode("utf-8")
            except UnicodeDecodeError:
                output.writestr(name, data)
                continue
            lines = []
            for line in decoded.splitlines():
                try:
                    lines.append(json.dumps(redact(json.loads(line)), ensure_ascii=False))
                except ValueError:
                    lines.append(redact(line))
            output.writestr(name, "\n".join(lines).encode())


if __name__ == "__main__":
    sources = sorted(Path("apps/web/test-results/android-cross-surface").rglob("trace.zip"))
    sources += sorted(Path("apps/web/test-results/android-cross-financial").rglob("trace.zip"))
    sources += sorted(Path("artifacts").glob("*-guest-trace.zip"))
    if not sources:
        print("SKIP: no browser trace was produced before the earlier failure")
        raise SystemExit(0)
    for index, source in enumerate(sources):
        export(source, Path(f"artifacts/sanitized-traces/{index}-{source.parent.name}.zip"))
    print(f"Exported {len(sources)} redacted trace archives; raw traces remain local")
