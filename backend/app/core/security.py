"""Security helpers for untrusted user, retrieval, and tool content."""

import re

_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)")
_LONG_IDENTIFIER = re.compile(r"\b\d{8,19}\b")
_UUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)


def redact_pii(value: str) -> str:
    """Remove common direct identifiers before model calls or protected logs."""

    protected: list[str] = []

    def protect_uuid(match: re.Match[str]) -> str:
        protected.append(match.group(0))
        return f"[SAFE_UUID_{len(protected) - 1}]"

    value = _UUID.sub(protect_uuid, value)
    value = _EMAIL.sub("[REDACTED_EMAIL]", value)
    value = _PHONE.sub("[REDACTED_PHONE]", value)
    value = _LONG_IDENTIFIER.sub("[REDACTED_IDENTIFIER]", value)
    for index, uuid in enumerate(protected):
        value = value.replace(f"[SAFE_UUID_{index}]", uuid)
    return value


def untrusted_evidence(value: str) -> str:
    """Label data as evidence so it cannot be confused with instructions."""

    return "<UNTRUSTED_EVIDENCE>\n" + redact_pii(value) + "\n</UNTRUSTED_EVIDENCE>"
