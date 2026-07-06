import type { Scan } from "../api/types";
import { StatusPill } from "./Badges";

const TOOL_LABELS: Record<string, string> = {
  sast: "SAST — Semgrep",
  sca: "SCA — Trivy",
  iac: "IaC — Trivy config",
  dast: "DAST — OWASP ZAP",
};

export default function ScanProgress({ scan }: { scan: Scan }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">Scan progress</h3>
        <StatusPill status={scan.status} />
      </div>
      <div className="space-y-2">
        {scan.scan_types.map((tool) => (
          <div key={tool} className="flex items-center justify-between rounded bg-gray-50 px-3 py-2">
            <span className="text-sm text-gray-700">{TOOL_LABELS[tool] ?? tool}</span>
            <StatusPill status={scan.tool_status?.[tool] ?? "queued"} />
          </div>
        ))}
      </div>
      {scan.error_message && (
        <p className="mt-3 rounded bg-red-50 p-2 text-xs text-red-700">{scan.error_message}</p>
      )}
    </div>
  );
}
