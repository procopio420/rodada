"""Encrypted logical backup via private SSH; restore ONLY in networkless local tmpfs."""

import hashlib
import json
import os
import shlex
import signal
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

EXPECTED_SHA = "c589ff0862b1a7702e12c20a00cffda6cb2f289e"
AAD = b"1ca79d6a-a555-4346-b4b6-72b0a7706359|ab6da311-0926-4b5a-ab86-1d21fe893e12|8a53ce2e-3923-43d2-98c5-590cffa0315b"
ROOT = Path.home() / ".local/share/rodada-secure-backups"
KEYS = Path.home() / ".config/rodada-backup-keys"
CONTAINER = "rodada-spec025-gate3-restore"
POSTGRES_SSH_USER = "5a1ea019-f0e0-41b3-a0d3-6b2fc0957fff"
# Resolve this instance through `railway ssh config --dry-run` before use.
SNAPSHOT_SQL = "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;\nSET LOCAL lock_timeout='2s';\nSET LOCAL statement_timeout='30s';\nSELECT pg_export_snapshot() AS snapshot_id \\gset\n\\setenv SPEC025_BACKUP_SNAPSHOT :snapshot_id\nSELECT json_build_object('source_version',current_setting('server_version'),'database_name',current_database(),'captured_at',clock_timestamp(),'table_counts',(SELECT json_object_agg(tablename,n) FROM (SELECT tablename,(xpath('/row/count/text()',query_to_xml(format('SELECT count(*) FROM %I.%I','public',tablename),false,true,'')))[1]::text::bigint AS n FROM pg_tables WHERE schemaname='public' ORDER BY tablename) counts),'read_only_exported_snapshot',current_setting('transaction_read_only')='on');\n\\! pg_dump --no-password --format=custom --snapshot=\"$SPEC025_BACKUP_SNAPSHOT\" --lock-wait-timeout=2s\n\\if :SHELL_ERROR\n\\quit 3\n\\endif\nCOMMIT;\n"
APP_GUARD = "import os,json; print(json.dumps({k:os.getenv(k) for k in ('RAILWAY_GIT_COMMIT_SHA','RAILWAY_DEPLOYMENT_ID','RODADA_ENABLE_TENANT_HOST_UI','RODADA_DEMO_SEED_ON_START')}))"


def run(command, **kwargs):
    result = subprocess.run(
        command, capture_output=True, timeout=180, check=False, **kwargs
    )
    if result.returncode:
        raise RuntimeError("Subprocess failed; raw output suppressed")
    return result.stdout


def main():
    if not __debug__:
        raise RuntimeError("Operational guards require Python assertions")
    os.umask(0o077)
    ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    KEYS.mkdir(parents=True, exist_ok=True, mode=0o700)
    assert ROOT.stat().st_mode & 0o077 == KEYS.stat().st_mode & 0o077 == 0
    base = "spec025-gate3-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    key = AESGCM.generate_key(bit_length=256)
    keypath = KEYS / (base + ".key")
    with keypath.open("xb") as handle:
        handle.write(key)
    archive = ROOT / (base + ".pgdump.aesgcm")
    started = time.monotonic()
    app_guard_command = [
        "ssh",
        "-T",
        "-o",
        "BatchMode=yes",
        "-i",
        str(Path.home() / ".ssh/rodada-spec025-audit"),
        "rodada-web-demo.up.railway.app@ssh.railway.com",
        "python -c " + shlex.quote(APP_GUARD),
    ]
    before = json.loads(run(app_guard_command))
    assert before["RAILWAY_GIT_COMMIT_SHA"] == EXPECTED_SHA
    assert (
        before["RODADA_DEMO_SEED_ON_START"] == "false"
        and before["RODADA_ENABLE_TENANT_HOST_UI"] == "false"
    )
    proc = subprocess.Popen(
        [
            "timeout",
            "180s",
            "ssh",
            "-T",
            "-o",
            "BatchMode=yes",
            "-i",
            str(Path.home() / ".ssh/rodada-spec025-audit"),
            POSTGRES_SSH_USER + "@ssh.railway.com",
            'PGHOST=127.0.0.1 PGPORT=5432 PGUSER="$POSTGRES_USER" PGDATABASE="$POSTGRES_DB" PGPASSWORD="$POSTGRES_PASSWORD" PGOPTIONS=\'-c default_transaction_read_only=on -c statement_timeout=120000 -c idle_in_transaction_session_timeout=180000\' psql -XqAtw -v ON_ERROR_STOP=1',
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    proc.stdin.write(SNAPSHOT_SQL.encode())
    proc.stdin.close()
    header = proc.stdout.readline(1024 * 1024)
    try:
        metadata = json.loads(header)
        assert metadata["read_only_exported_snapshot"]
        nonce = os.urandom(12)
        encryptor = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
        encryptor.authenticate_additional_data(AAD)
        digest_state = hashlib.sha256()
        dump_bytes = 0
        prefix = b""
        with archive.open("xb") as handle:
            handle.write(b"R025B01" + nonce)
            while chunk := proc.stdout.read(65536):
                if not prefix:
                    prefix = chunk[:5]
                dump_bytes += len(chunk)
                assert dump_bytes <= 64 * 1024 * 1024
                digest_state.update(chunk)
                handle.write(encryptor.update(chunk))
            diagnostics = proc.stderr.read()
            assert proc.wait(timeout=150) == 0 and not diagnostics
            assert prefix == b"PGDMP"
            handle.write(encryptor.finalize())
            handle.write(encryptor.tag)
        assert json.loads(run(app_guard_command)) == before
        metadata.update(sha=EXPECTED_SHA, deployment=before["RAILWAY_DEPLOYMENT_ID"])
        digest = digest_state.hexdigest()
        # Authenticate retained bytes before passing plaintext to a local restore.
        retained = archive.read_bytes()
        plaintext = AESGCM(keypath.read_bytes()).decrypt(
            retained[7:19], retained[19:], AAD
        )
        assert hashlib.sha256(plaintext).hexdigest() == digest
        run(
            [
                "docker",
                "run",
                "--detach",
                "--rm",
                "--name",
                CONTAINER,
                "--network",
                "none",
                "--tmpfs",
                "/var/lib/postgresql:rw,noexec,nosuid,size=536870912",
                "-e",
                "POSTGRES_HOST_AUTH_METHOD=trust",
                "-e",
                "POSTGRES_USER=spec025_restore",
                "-e",
                "POSTGRES_DB=spec025_restore",
                "postgres:18",
            ]
        )
        try:
            for _ in range(60):
                ready = subprocess.run(
                    [
                        "docker",
                        "exec",
                        CONTAINER,
                        "pg_isready",
                        "-U",
                        "spec025_restore",
                        "-d",
                        "spec025_restore",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                if (
                    ready.returncode == 0
                    and run(
                        ["docker", "exec", CONTAINER, "cat", "/proc/1/comm"]
                    ).strip()
                    == b"postgres"
                ):
                    break
                time.sleep(0.5)
            else:
                raise RuntimeError("Disposable restore did not become ready")
            restore_started = time.monotonic()
            run(
                [
                    "docker",
                    "exec",
                    "-i",
                    CONTAINER,
                    "pg_restore",
                    "--exit-on-error",
                    "--no-owner",
                    "--no-acl",
                    "-U",
                    "spec025_restore",
                    "-d",
                    "spec025_restore",
                ],
                input=plaintext,
            )
            query = (
                "SELECT json_object_agg(tablename,n) FROM ("
                + " UNION ALL ".join(
                    "SELECT '"
                    + t.replace("'", "''")
                    + "' AS tablename,count(*) AS n FROM public.\""
                    + t.replace('"', '""')
                    + '"'
                    for t in metadata["table_counts"]
                )
                + ") counts;"
            )
            restored_counts = json.loads(
                run(
                    [
                        "docker",
                        "exec",
                        "-i",
                        CONTAINER,
                        "psql",
                        "-X",
                        "-At",
                        "-v",
                        "ON_ERROR_STOP=1",
                        "-U",
                        "spec025_restore",
                        "-d",
                        "spec025_restore",
                    ],
                    input=query.encode(),
                )
            )
            assert restored_counts == metadata["table_counts"]
            invalid = run(
                [
                    "docker",
                    "exec",
                    CONTAINER,
                    "psql",
                    "-X",
                    "-At",
                    "-U",
                    "spec025_restore",
                    "-d",
                    "spec025_restore",
                    "-c",
                    "SELECT count(*) FROM pg_constraint WHERE connamespace='public'::regnamespace AND NOT convalidated;",
                ]
            )
            assert int(invalid.strip()) == 0
            restore_seconds = time.monotonic() - restore_started
        finally:
            run(["docker", "rm", "--force", CONTAINER])
        verified = datetime.now(timezone.utc)
        receipt = {
            "logical_backup_reference": "logical-sha256:" + digest,
            "source_sha": EXPECTED_SHA,
            "source_deployment": metadata["deployment"],
            "source_version": metadata["source_version"],
            "tables_verified": len(restored_counts),
            "all_same_snapshot_counts_match": True,
            "all_restored_constraints_validated": True,
            "dump_bytes": dump_bytes,
            "restore_seconds": round(restore_seconds, 3),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "verified_at": verified.isoformat(),
            "retention_review_at": (verified + timedelta(days=7)).date().isoformat(),
            "archive_authenticated": True,
            "custody_owner_only": True,
            "key_separate": True,
            "restored_copy_removed": True,
            "restore_container_removed": True,
            "limits": "Logical snapshot, not PITR/cluster roles/ACL/financial reconciliation sign-off; no operational restore.",
        }
        manifest = {
            **metadata,
            "archive_sha256": digest,
            "encrypted_sha256": hashlib.sha256(retained).hexdigest(),
            "verified_at": receipt["verified_at"],
            "recovery_receipt": receipt,
        }
        manifest_nonce = os.urandom(12)
        with (ROOT / (base + ".manifest.aesgcm")).open("xb") as handle:
            handle.write(
                manifest_nonce
                + AESGCM(key).encrypt(
                    manifest_nonce, json.dumps(manifest).encode(), AAD
                )
            )
        with (ROOT / (base + ".receipt.json")).open("x") as handle:
            json.dump(receipt, handle, indent=2)
        print(json.dumps(receipt))
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001 -- Never log private backup errors/data.
        print(
            json.dumps(
                {
                    "backup_recovery": "FAILED",
                    "error_class": type(error).__name__,
                    "raw_suppressed": True,
                }
            )
        )
        raise SystemExit(1)
