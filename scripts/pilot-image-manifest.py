#!/usr/bin/env python3
"""Record the immutable local staging image and runtime versions, without secrets."""
import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def output(*command):
    return subprocess.check_output(command, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--container", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--evidence", required=True)
    args = parser.parse_args()
    # Require a real commit; callers must supply the commit actually built.
    sha = output("git", "rev-parse", args.source_sha + "^{commit}")
    image_id = output("docker", "image", "inspect", args.image, "--format", "{{.Id}}")
    running_id = output("docker", "inspect", args.container, "--format", "{{.Image}}")
    if image_id != running_id:
        parser.error("Container does not run the selected immutable image")
    versions = json.loads(output(
        "docker", "exec", args.container, "python", "-c",
        "import importlib.metadata,json,platform; print(json.dumps({'python':platform.python_version(),**{p:importlib.metadata.version(p) for p in ['Django','djangorestframework','psycopg','uvicorn']}}))",
    ))
    versions["node"] = output("docker", "exec", args.container, "node", "--version")
    versions["next"] = output("docker", "exec", args.container, "node", "-p",
                              "require('/app/apps/web/node_modules/next/package.json').version")
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "source_sha_declared_by_builder": sha,
        "image_id": image_id,
        "container_image_matches": True,
        "versions": versions,
        "limits": ["Local image identity; does not attest a Railway deployed SHA",
                   "Rebuilds resolve floating dependencies; promote this image by digest or archive"],
    }
    Path(args.evidence).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
