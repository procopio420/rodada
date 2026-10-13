# GitHub Actions policy

The pilot is web-first. Pull requests should verify the code they touch without launching
a full release/homologation suite on every commit.

| Workflow | Automatic | Manual | Purpose |
| --- | --- | --- | --- |
| API | PR/push changing `apps/api/**` | Yes | Django checks, migration drift and one full PostgreSQL pytest run |
| Web | PR/push changing web, API, prototype or this workflow | Yes | Next.js build, typecheck, auth, visual and real BFF integration tests |
| Android | PR/push changing Android | Yes | Unit tests and debug build; release AAB smoke on main/manual only |
| Android real POST disconnect | No | Yes | Two emulator + backend network-failure tests |
| Aderlan isolated pilot shift acceptance | No | Yes | Full disposable PostgreSQL shift |
| Railway Aderlan demo Docker smoke | PR changing Railway deployment or staging smoke script | Yes | Build full Railway container and smoke runtime |
| Integrated release demo | No | Yes | Restart/concurrency and full shift gate |
| Play Store internal release | No | Yes | Signed AAB and optional explicit Google Play upload |

## Release/homologation gates

- Keep **API** and **Web** as the normal PR gates for the web pilot.
- Run **Railway Aderlan demo Docker smoke** manually before changes that materially
  affect packaging/startup or a major pilot deployment; edits to `deploy/railway/**`
  still trigger it automatically.
- Run **Aderlan isolated pilot shift acceptance** and/or **Integrated release demo**
  manually before a high-impact release or operational homologation.
- For Android releases, run **Android** manually (including force-stop recovery) and
  **Android real POST disconnect** when payment/offline/network recovery logic changes.
  **Play Store internal release** remains explicitly dispatched; it is never invoked
  by ordinary PR/push and uploading to Play remains opt-in.
- `concurrency` discards superseded **PR** runs, never ongoing `main` or
  `workflow_dispatch` runs. Existing runs started before this policy may still
  require cancellation through the GitHub Actions UI.

This change modifies workflow scheduling and removes the duplicated API job,
but **does not delete the underlying tests**.
