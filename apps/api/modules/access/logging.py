import logging
import re

_TOKEN_RE = re.compile(r"\b(?:rat|rrt)_[A-Za-z0-9_-]+\b")
_BEARER_RE = re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+")
_JSON_PIN_RE = re.compile(r'(?i)("pin"\s*:\s*")[^"]*(")')
_KV_PIN_RE = re.compile(r"(?i)(\bpin\s*=\s*)[^\s,;]+")


def redact_auth_secrets(value: str) -> str:
    redacted = _TOKEN_RE.sub("[REDACTED_TOKEN]", value)
    redacted = _BEARER_RE.sub(r"\1[REDACTED_TOKEN]", redacted)
    redacted = _JSON_PIN_RE.sub(r"\1[REDACTED_PIN]\2", redacted)
    redacted = _KV_PIN_RE.sub(r"\1[REDACTED_PIN]", redacted)
    return redacted


class CredentialRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_auth_secrets(record.getMessage())
        record.args = ()
        return True
