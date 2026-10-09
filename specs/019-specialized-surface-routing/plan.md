# Plan

1. Resolve known production and legacy hostnames to an internal surface route.
2. Keep local routes as explicit compatibility entry points.
3. Generate host-specific metadata and web manifests from one codebase.
4. Add focused surface navigation where the surface owns several manager jobs.
5. Reconcile PR #40 by merging current main without rewriting its author's commit.
6. Consolidate operational layouts, loading/error/stale feedback, accessible
   controls and canonical manifest colors. Remove personal attribution from the shared shell.
7. Compare identical prototype primitives with strict pixel assertions; document
   full-screen differences where workflows differ. Cover five widths and eight
   existing routes, plus warning, saving, loading, error, empty and crowded states.
8. Enforce visual/a11y and real Django/BFF workflows in Web CI. Keep fixture data
   disposable; use PostgreSQL in CI and isolated SQLite for local smoke checks.
