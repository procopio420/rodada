"""Test-only cross-process coordination for PostgreSQL Web E2E resets.

The Playwright API subprocess runs a background realtime publisher while a
separate seed subprocess issues PostgreSQL TRUNCATE between spec files. A
shared/exclusive POSIX flock prevents that publisher from querying half-reset
tables or deadlocking TRUNCATE. Normal API processes never import this module.
"""
import errno
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

if os.name == "nt":
    import msvcrt
else:
    import fcntl


@contextmanager
def file_lock(path: Path, *, exclusive: bool):
    """Cross-process lock held for the *entire* operation, not just acquisition."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.open("a+b") as lock_file:
        if os.name == "nt":
            # Windows readers serialize too: stronger exclusion, same reset safety.
            if path.stat().st_size == 0:
                lock_file.write(b"0")
                lock_file.flush()
            lock_file.seek(0)
            while True:
                try:
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError as error:
                    if error.errno not in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                        raise
                    time.sleep(0.05)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


@contextmanager
def e2e_database_guard(*, exclusive: bool):
    # SQLite uses its own disposable file; do not coordinate with PostgreSQL.
    if os.environ.get("RODADA_E2E_POSTGRES") != "1":
        yield
        return

    from django.conf import settings

    db = settings.DATABASES["default"]
    if (
        db.get("NAME") != "rodada_web_e2e"
        or db.get("HOST") not in {"127.0.0.1", "localhost"}
        or not db.get("ENGINE", "").endswith("postgresql")
    ):
        raise RuntimeError("E2E database lock requires local PostgreSQL rodada_web_e2e")

    # One lock for every subprocess sharing this disposable DB, across test runs.
    identity = "windows" if os.name == "nt" else str(os.getuid())
    private_dir = Path(tempfile.gettempdir()) / f"rodada-e2e-{identity}"
    with file_lock(private_dir / "rodada_web_e2e.lock", exclusive=exclusive):
        yield


def _sqlstate(error: BaseException) -> str | None:
    """Unwrap Django OperationalError and psycopg 2/3 database exceptions."""
    seen = set()
    while error is not None and id(error) not in seen:
        seen.add(id(error))
        code = getattr(error, "sqlstate", None) or getattr(error, "pgcode", None)
        if code:
            return str(code)
        error = error.__cause__ or error.__context__
    return None


def retry_transient_reset(operation, *, max_attempts: int = 4) -> None:
    """Retry *only* PostgreSQL deadlock/lock timeout, with a hard bound.

    TRUNCATE is transactional; after a deadlock PostgreSQL rolls the statement
    back, allowing a fresh attempt. Never retry unknown errors or silently
    pretend a reset happened.
    """
    for attempt in range(max_attempts):
        try:
            operation()
            return
        except Exception as error:
            if _sqlstate(error) not in {"40P01", "55P03"} or attempt == max_attempts - 1:
                raise
            time.sleep(0.25 * (2 ** attempt))
