# Acceptance container packaging — 2026-10-12

The new secure-runtime regression reads `deploy/railway/runtime-profile.sh`.
The disposable demo API image previously copied only API/print bridge files, so
running the full API suite inside that image would miss the preflight resource.
The image now includes that exact source file. It still starts the same API command;
no demo/pilot startup mode or domain behavior changes.

Fresh `docker build -f demo/api.Dockerfile` and actual image execution of
`python -m pytest tests/test_railway_runtime_profile.py`: **7 passed** (0.34s).
Final integrated full PostgreSQL/container gates remain separate.
