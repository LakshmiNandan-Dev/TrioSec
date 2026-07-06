import json
import subprocess

from app.scanners import severity
from app.scanners.base import RawFinding, ScanContext, ScannerAdapter


class TrivyAdapter(ScannerAdapter):
    name = "trivy"

    def run(self, ctx: ScanContext) -> list[RawFinding]:
        cmd = [
            "trivy", "fs",
            "--format", "json",
            "--scanners", "vuln,secret",
            "--quiet",
            "--timeout", "15m",
            ".",
        ]
        ctx.log("trivy: scanning filesystem for vulnerable dependencies and secrets")
        proc = subprocess.run(cmd, cwd=ctx.scan_root, capture_output=True, text=True, timeout=1800)
        if proc.returncode != 0:
            raise RuntimeError(f"trivy exited {proc.returncode}: {proc.stderr.strip()[-500:]}")

        data = json.loads(proc.stdout or "{}")
        findings = []
        for result in data.get("Results") or []:
            target = result.get("Target")

            for vuln in result.get("Vulnerabilities") or []:
                vuln_id = vuln.get("VulnerabilityID")
                pkg = vuln.get("PkgName")
                cwe_ids = vuln.get("CweIDs") or []
                raw = {k: v for k, v in vuln.items() if k != "Description"}
                findings.append(
                    RawFinding(
                        tool="trivy",
                        category="sca",
                        severity=severity.from_trivy(vuln.get("Severity")),
                        title=vuln.get("Title") or f"{vuln_id} in {pkg}",
                        description=vuln.get("Description"),
                        rule_id=vuln_id,
                        cwe=cwe_ids[0] if cwe_ids else None,
                        cve=vuln_id,
                        file_path=target,
                        package_name=pkg,
                        installed_version=vuln.get("InstalledVersion"),
                        fixed_version=vuln.get("FixedVersion"),
                        remediation=vuln.get("PrimaryURL"),
                        raw=raw,
                    )
                )

            for secret in result.get("Secrets") or []:
                # Never persist the matched secret content itself.
                raw = {k: v for k, v in secret.items() if k not in ("Code", "Match")}
                findings.append(
                    RawFinding(
                        tool="trivy",
                        category="secret",
                        severity=severity.from_trivy(secret.get("Severity")),
                        title=secret.get("Title") or f"Secret: {secret.get('RuleID')}",
                        description=f"Hardcoded secret detected ({secret.get('Category')})",
                        rule_id=secret.get("RuleID"),
                        file_path=target,
                        line_start=secret.get("StartLine"),
                        line_end=secret.get("EndLine"),
                        remediation="Remove the secret from the codebase and rotate the credential.",
                        raw=raw,
                    )
                )
        ctx.log(f"trivy: {len(findings)} findings")
        return findings
