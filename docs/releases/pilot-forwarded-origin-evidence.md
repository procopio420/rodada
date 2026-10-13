# Pilot forwarded origin correction — 2026-10-12

Fresh pinned staging probe reproduced HTTP 403 for BFF login with correct `Origin: http://127.0.0.1:18095`: Nginx `$host` discarded the explicit port, so the existing strict BFF Origin/Host check correctly rejected the altered authority. Preserve `$http_host` in Host and X-Forwarded-Host; CSRF implementation stays unchanged.

Actual disposable Nginx/Next/Django runtime was tested after replacing only those two directives and reloading validated Nginx configuration. Correct Origin plus same-origin Fetch Metadata returned 200; different port, unrelated origin and cross-site metadata all returned 403. No token/PIN is recorded. The same four assertions now run in Railway Docker smoke. This is HTTP-client origin validation, not physical-device or public HTTPS browser acceptance. The patched previous container is no longer evidence of an unmodified pinned image; final release rebuild/restart must use the integrated SHA.
