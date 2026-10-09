#!/usr/bin/env python3
"""Re-extract reference ZIPs, using local fonts and safe DC image bindings."""

import hashlib
import json
import re
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXPORTS = [
    ("Protótipo", "night", "Uma noite no bar"),
    ("Sistema", "system", "Sistema Rodada"),
    ("Tela", "kitchen", "Tela da Cozinha"),
    ("Modo", "peak", "Modo pico"),
    ("Sem", "connectivity", "Sem sinal → Sincronizado"),
]


def main():
    root = REPO / "prototype/references"
    root.mkdir(exist_ok=True)
    entries = []
    for prefix, slug, label in EXPORTS:
        archive = next((REPO / "prototype").glob(prefix + "*.zip"))
        destination = root / slug
        destination.mkdir(exist_ok=True)
        with zipfile.ZipFile(archive) as export:
            for name in export.namelist():
                target = destination / name
                if not target.resolve().is_relative_to(destination.resolve()):
                    raise ValueError(f"Unsafe archive member: {name}")
                if name.endswith("/"):
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(export.read(name))
            entry = next(name for name in export.namelist() if name.endswith(".html"))
        html = (destination / entry).read_text()
        # The runtime already maps sc-camel-src to src after interpolation.
        # This avoids browser requests for literal {{...}} URLs before mount.
        html = re.sub(r'\bsrc=("\{\{[^"<>]+\}\}")', r'sc-camel-src=\1', html)
        html = re.sub(
            r'<link rel="stylesheet" href="https://fonts.googleapis.com/[^>]+>',
            '<link rel="stylesheet" href="../../fonts/fonts.css">',
            html,
        )
        (destination / entry).write_text(html)
        entries.append({
            "id": slug, "title": label, "archive": archive.name,
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "entry": slug + "/" + entry,
        })
    (root / "manifest.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=2) + "\n"
    )
    links = "".join(
        f'<li><a class="button button--secondary" style="display:block;text-decoration:none" '
        f'href="{entry["entry"]}">{entry["title"]}</a></li>'
        for entry in entries
    )
    (root / "index.html").write_text(f'''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Rodada · referências da noite</title><link rel="stylesheet" href="../design-system.css"><main class="app-shell"><h1>Referências da noite</h1><p>Simulações para revisão de produto. Dados e ações são demonstrativos.</p><ul style="list-style:none;padding:0;display:grid;gap:var(--space-3)">{links}</ul><p><a href="../index.html">Protótipo anterior</a> · <a href="../../docs/design/prototype-integration.md">Contrato de integração</a></p></main></html>''')


if __name__ == "__main__":
    main()
