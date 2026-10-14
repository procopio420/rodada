"""Standalone typed v1 wire/driver boundaries. No dependency on Django."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, Protocol, TypedDict

PROTOCOL_VERSION = 1


class CapabilityEvidence(StrEnum):
    SUGGESTED = "SUGGESTED"
    VERIFIED_BY_TEST = "VERIFIED_BY_TEST"
    UNSUPPORTED = "UNSUPPORTED"


class AgentState(StrEnum):
    PENDING_PAIRING = "PENDING_PAIRING"
    ONLINE = "ONLINE"
    STALE = "STALE"
    OFFLINE = "OFFLINE"
    REVOKED = "REVOKED"


class PrinterHealth(StrEnum):
    UNKNOWN = "UNKNOWN"
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"


class SubmissionOutcome(StrEnum):
    OUTPUT_READY = "OUTPUT_READY"
    SPOOL_ACCEPTED = "SPOOL_ACCEPTED"
    DELIVERY_UNCERTAIN = "DELIVERY_UNCERTAIN"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_FINAL = "FAILED_FINAL"


class TransportKind(StrEnum):
    WINDOWS_RAW = "WINDOWS_RAW"
    WINDOWS_DRIVER = "WINDOWS_DRIVER"
    WINDOWS_SHARED = "WINDOWS_SHARED"
    TCP_LAN = "TCP_LAN"


class ContractResponse(TypedDict):
    protocol_version: Literal[1]
    agent_id: str
    venue_id: str
    scope: Literal["PRINT_AGENT_V1"]
    operations: list[str]
    delivery_enabled: bool


@dataclass(frozen=True)
class PrinterCapabilities:
    width_mm: Literal[58, 80]
    raw_escpos: CapabilityEvidence = CapabilityEvidence.UNSUPPORTED
    cut: CapabilityEvidence = CapabilityEvidence.UNSUPPORTED
    qr: CapabilityEvidence = CapabilityEvidence.UNSUPPORTED
    status: CapabilityEvidence = CapabilityEvidence.UNSUPPORTED


@dataclass(frozen=True)
class RenderedOutput:
    content: bytes
    mode: Literal["RAW", "WINDOWS_RENDERED"]


@dataclass(frozen=True)
class SubmissionResult:
    outcome: SubmissionOutcome
    # FAILED_RETRYABLE is valid only if adapter proves no side effect began.
    spool_id: str | None = None


class PrinterDriver(Protocol):
    def render(
        self, text: str, capabilities: PrinterCapabilities
    ) -> RenderedOutput: ...


class PrinterTransport(Protocol):
    def submit(
        self, output: RenderedOutput, *, attempt_token: str
    ) -> SubmissionResult: ...
