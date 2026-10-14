#!/usr/bin/env python3
"""Reproducible full-source lint inventory for the Rodada cleanup campaign.

This is deliberately advisory while legacy diagnostics remain; use --strict once
the baseline is zero. Does not modify source or suppress diagnostics.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def run_json(argv: list[str], cwd: Path) -> list[dict]:
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode not in (0, 1):
        raise RuntimeError(f"{argv[0]} failed ({result.returncode}): {result.stderr[:1000]}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{argv[0]} returned invalid JSON: {result.stderr[:1000]}") from exc
    if not isinstance(value, list):
        raise RuntimeError(f"{argv[0]} returned non-list diagnostics")
    return value


def relative(filename: str) -> str:
    try:
        return Path(filename).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return filename


def collect() -> list[dict]:
    findings: list[dict] = []
    for diagnostic in run_json(
        [sys.executable, "-m", "ruff", "check", "apps/api",
         "--output-format", "json", "--select", "E4,E7,E9,F"], ROOT
    ):
        findings.append({
            "area": "api",
            "path": relative(diagnostic["filename"]),
            "line": diagnostic["location"]["row"],
            "rule": diagnostic["code"],
            "severity": "error",
            "message": diagnostic["message"],
        })

    for file in run_json(
        ["node_modules/.bin/eslint", ".", "--format", "json"], ROOT / "apps/web"
    ):
        for diagnostic in file.get("messages", []):
            findings.append({
                "area": "web",
                "path": relative(file["filePath"]),
                "line": diagnostic.get("line") or 0,
                "rule": diagnostic.get("ruleId") or "ESLINT_FATAL",
                "severity": "error" if diagnostic.get("severity") == 2 else "warning",
                "message": diagnostic.get("message", ""),
            })
    return sorted(findings, key=lambda item: (
        item["area"], item["path"], item["line"], item["rule"]
    ))


def markdown(findings: list[dict]) -> str:
    areas = Counter(row["area"] for row in findings)
    rules = Counter((row["area"], row["rule"]) for row in findings)
    paths = Counter((row["area"], row["path"]) for row in findings)
    lines = [
        "# Rodada — full-source static quality inventory",
        "",
        f"API (Ruff E4/E7/E9/F): **{areas['api']}**",
        f"Web (ESLint/Next): **{areas['web']}**",
        f"Total: **{len(findings)}**",
        "",
        "These are current diagnostics, NOT confirmed defects or production incidents.",
        "The incremental quality gates run separately; passing them does not imply zero debt.",
        "",
        "## Most frequent rules",
        "",
        "| Area | Rule | Count |",
        "| --- | --- | ---: |",
    ]
    lines.extend(f"| {area} | `{rule}` | {count} |"
                 for (area, rule), count in rules.most_common(25))
    lines.extend(["", "## Most affected files", "",
                  "| Area | Path | Count |", "| --- | --- | ---: |"])
    lines.extend(f"| {area} | `{path}` | {count} |"
                 for (area, path), count in paths.most_common(30))
    lines.extend(["", "## Every diagnostic", ""])
    lines.extend(f"- `{row['path']}:{row['line']}` [{row['rule']}] "
                 + row["message"].replace("\n", " ")
                 for row in findings)
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("quality-debt"))
    parser.add_argument("--strict", action="store_true",
                        help="Fail when ANY API or Web finding remains")
    args = parser.parse_args()
    try:
        findings = collect()
    except (RuntimeError, OSError, KeyError, TypeError) as exc:
        print(f"QUALITY INVENTORY FAILED: {exc}", file=sys.stderr)
        return 2
    output = args.out_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "findings.json").write_text(
        json.dumps(findings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    summary = markdown(findings)
    (output / "summary.md").write_text(summary, encoding="utf-8")
    print(summary)
    step_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if step_summary:
        with Path(step_summary).open("a", encoding="utf-8") as stream:
            stream.write(summary + "\n")
    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
