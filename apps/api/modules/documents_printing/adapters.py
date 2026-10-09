"""Hardware boundary. Success means transport/spool acceptance, never paper proof."""

import os
import shutil
import socket
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class DeliveryResult:
    outcome: str
    detail: str = ""


class PrintAdapter(Protocol):
    def deliver(self, job_id: str, payload: bytes) -> DeliveryResult: ...


class FileAdapter:
    def __init__(self, directory):
        self.directory = Path(directory)

    def deliver(self, job_id, payload):
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=self.directory, delete=False) as output:
                temporary = output.name
                output.write(payload)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.directory / (job_id + ".html"))
        except OSError:
            return DeliveryResult("FAILED_RETRYABLE", "Arquivo local não gravado.")
        return DeliveryResult("OUTPUT_READY", "HTML gerado; nenhuma impressão física executada.")


class NetworkAdapter:
    def __init__(self, host, port=9100, timeout=5):
        self.host, self.port, self.timeout = host, port, timeout

    def deliver(self, job_id, payload):
        try:
            connection = socket.create_connection((self.host, self.port), self.timeout)
        except OSError:
            return DeliveryResult("FAILED_RETRYABLE", "Conexão recusada antes de enviar dados.")
        try:
            with connection:
                connection.sendall(payload)
        except OSError:
            return DeliveryResult(
                "DELIVERY_UNCERTAIN", "Envio interrompido; pode haver impressão parcial."
            )
        return DeliveryResult("SPOOL_ACCEPTED", "Bytes enviados ao destino; papel não confirmado.")


class SpoolAdapter:
    def __init__(self, queue, executable="lp"):
        self.queue, self.executable = queue, executable

    def deliver(self, job_id, payload):
        if not shutil.which(self.executable):
            return DeliveryResult(
                "FAILED_RETRYABLE", "Spooler local não instalado; dados não enviados."
            )
        try:
            result = subprocess.run(
                [self.executable, "-d", self.queue, "-o", "raw", "-t", "Rodada-" + job_id],
                input=payload,
                capture_output=True,
                timeout=10,
                check=False,
            )
        except FileNotFoundError:
            return DeliveryResult("FAILED_RETRYABLE", "Spooler ausente antes de envio.")
        except (OSError, subprocess.TimeoutExpired):
            return DeliveryResult(
                "DELIVERY_UNCERTAIN", "Spooler interrompido; confira fila e papel."
            )
        if result.returncode:
            return DeliveryResult(
                "DELIVERY_UNCERTAIN", "Spooler informou erro; aceitação parcial não descartada."
            )
        return DeliveryResult("SPOOL_ACCEPTED", "Spooler aceitou o trabalho; papel não confirmado.")
