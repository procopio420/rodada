import logging
import re

_TOKEN_RE = re.compile(r"\b(?:rat|rrt)_[A-Za-z0-9_-]+\b")
_RECEIPT_URL_RE = re.compile(r"(/(?:receipts?|api/receipt)/)[A-Za-z0-9_-]{43}(?=/|$)")
_BEARER_RE = re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+")
_JSON_PIN_RE = re.compile(r'(?i)("pin"\s*:\s*")[^"]*(")')
_KV_PIN_RE = re.compile(r"(?i)(\bpin\s*=\s*)[^\s,;]+")


def redact_auth_secrets(value: str) -> str:
    redacted = _TOKEN_RE.sub("[REDACTED_TOKEN]", value)
    redacted = _RECEIPT_URL_RE.sub(
        lambda match: match.group(1) + "[REDACTED_RECEIPT_TOKEN]", redacted
    )
    redacted = _BEARER_RE.sub(r"\1[REDACTED_TOKEN]", redacted)
    redacted = _JSON_PIN_RE.sub(r"\1[REDACTED_PIN]\2", redacted)
    redacted = _KV_PIN_RE.sub(r"\1[REDACTED_PIN]", redacted)
    return redacted


class CredentialRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_auth_secrets(record.getMessage())
        record.args = ()
        return True
