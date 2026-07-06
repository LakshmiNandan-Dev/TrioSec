from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class RawFinding:
    tool: str
    category: str  # sast | sca | secret | dast
    severity: str  # critical | high | medium | low | info
    title: str
    description: str | None = None
    rule_id: str | None = None
    cwe: str | None = None
    cve: str | None = None
    file_path: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    url: str | None = None
    package_name: str | None = None
    installed_version: str | None = None
    fixed_version: str | None = None
    remediation: str | None = None
    raw: dict = field(default_factory=dict)


@dataclass
class ScanContext:
    scan_root: str | None
    dast_url: str | None
    dast_full_scan: bool
    semgrep_config: str
    log: Callable[[str], None]


class ScannerAdapter(ABC):
    name: str

    @abstractmethod
    def run(self, ctx: ScanContext) -> list[RawFinding]: ...
