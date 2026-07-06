import json
import subprocess

from app.scanners import severity
from app.scanners.base import RawFinding, ScanContext, ScannerAdapter


class SemgrepAdapter(ScannerAdapter):
    name = "semgrep"

    def run(self, ctx: ScanContext) -> list[RawFinding]:
        cmd = [
            "semgrep", "scan",
            "--config", ctx.semgrep_config,
            "--json", "--quiet", "--metrics=off",
            "--timeout", "300",
            ".",
        ]
        ctx.log(f"semgrep: running with config {ctx.semgrep_config}")
        proc = subprocess.run(cmd, cwd=ctx.scan_root, capture_output=True, text=True, timeout=1800)
        # 0 = clean run, 1 = findings reported; anything else is a real failure.
        if proc.returncode not in (0, 1):
            raise RuntimeError(f"semgrep exited {proc.returncode}: {proc.stderr.strip()[-500:]}")

        # An import-time crash also exits 1 but leaves stdout empty/non-JSON — treat that
        # as a failure rather than silently reporting zero findings.
        try:
            data = json.loads(proc.stdout)
        except (json.JSONDecodeError, TypeError) as exc:
            raise RuntimeError(
                f"semgrep produced no JSON output: {proc.stderr.strip()[-500:]}"
            ) from exc
        findings = []
        for result in data.get("results", []):
            extra = result.get("extra", {}) or {}
            meta = extra.get("metadata", {}) or {}

            cwe = meta.get("cwe")
            if isinstance(cwe, list):
                cwe = cwe[0] if cwe else None
            if cwe:
                cwe = str(cwe).split(":")[0].strip()[:32]

            message = (extra.get("message") or result.get("check_id") or "").strip()
            title = (message.splitlines() or ["(no message)"])[0][:300]
            references = meta.get("references") or []
            remediation = extra.get("fix") or ("\n".join(references[:5]) if references else None)

            raw = dict(result)
            raw.get("extra", {}).pop("lines", None)  # avoid persisting source code excerpts

            findings.append(
                RawFinding(
                    tool="semgrep",
                    category="sast",
                    severity=severity.from_semgrep(extra.get("severity")),
                    title=title,
                    description=message,
                    rule_id=result.get("check_id"),
                    cwe=cwe,
                    file_path=result.get("path"),
                    line_start=(result.get("start") or {}).get("line"),
                    line_end=(result.get("end") or {}).get("line"),
                    remediation=remediation,
                    raw=raw,
                )
            )
        ctx.log(f"semgrep: {len(findings)} findings")
        return findings
