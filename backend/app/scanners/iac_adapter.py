import json
import subprocess

from app.scanners import severity
from app.scanners.base import RawFinding, ScanContext, ScannerAdapter


class TrivyIacAdapter(ScannerAdapter):
    """Infrastructure-as-Code misconfiguration scanning via Trivy.

    Covers Terraform, Kubernetes, Dockerfile, CloudFormation, Helm, ARM, etc.
    """

    name = "trivy-iac"

    def run(self, ctx: ScanContext) -> list[RawFinding]:
        cmd = [
            "trivy", "config",
            "--format", "json",
            "--quiet",
            "--timeout", "15m",
            ".",
        ]
        ctx.log("iac: scanning infrastructure-as-code for misconfigurations")
        proc = subprocess.run(cmd, cwd=ctx.scan_root, capture_output=True, text=True, timeout=1800)
        if proc.returncode != 0:
            raise RuntimeError(f"trivy config exited {proc.returncode}: {proc.stderr.strip()[-500:]}")

        try:
            data = json.loads(proc.stdout)
        except (json.JSONDecodeError, TypeError) as exc:
            raise RuntimeError(
                f"trivy config produced no JSON output: {proc.stderr.strip()[-500:]}"
            ) from exc

        findings = []
        for result in data.get("Results") or []:
            target = result.get("Target")
            for misc in result.get("Misconfigurations") or []:
                # Trivy reports PASS checks too when asked; keep only failures.
                if misc.get("Status") == "PASS":
                    continue
                cause = misc.get("CauseMetadata") or {}
                start_line = cause.get("StartLine") or None
                raw = {k: v for k, v in misc.items() if k not in ("Code",)}
                findings.append(
                    RawFinding(
                        tool="trivy",
                        category="iac",
                        severity=severity.from_trivy(misc.get("Severity")),
                        title=misc.get("Title") or misc.get("ID") or "Misconfiguration",
                        description=misc.get("Message") or misc.get("Description"),
                        rule_id=misc.get("ID") or misc.get("AVDID"),
                        file_path=target,
                        line_start=start_line if start_line and start_line > 0 else None,
                        remediation=misc.get("Resolution") or misc.get("PrimaryURL"),
                        raw=raw,
                    )
                )
        ctx.log(f"iac: {len(findings)} findings")
        return findings
