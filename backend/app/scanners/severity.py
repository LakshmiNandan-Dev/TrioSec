"""Per-tool severity → canonical (critical | high | medium | low | info)."""

_SEMGREP = {"ERROR": "high", "WARNING": "medium", "INFO": "info"}
_TRIVY = {"CRITICAL": "critical", "HIGH": "high", "MEDIUM": "medium", "LOW": "low", "UNKNOWN": "info"}
_ZAP = {"high": "high", "medium": "medium", "low": "low", "informational": "info"}


def from_semgrep(value: str | None) -> str:
    return _SEMGREP.get((value or "").upper(), "info")


def from_trivy(value: str | None) -> str:
    return _TRIVY.get((value or "").upper(), "info")


def from_zap(risk: str | None) -> str:
    return _ZAP.get((risk or "").lower(), "info")
