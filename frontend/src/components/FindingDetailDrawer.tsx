import type { Finding } from "../api/types";
import { SeverityBadge, ToolBadge } from "./Badges";

function Field({ label, value }: { label: string; value: string | number | null | undefined }) {
  if (value === null || value === undefined || value === "") return null;
  return (
    <div>
      <dt className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">{label}</dt>
      <dd className="break-all text-sm text-gray-800">{value}</dd>
    </div>
  );
}

export default function FindingDetailDrawer({
  finding,
  onClose,
}: {
  finding: Finding;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-40" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="absolute right-0 top-0 h-full w-full max-w-xl overflow-y-auto bg-white p-6 shadow-2xl">
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 className="text-base font-bold text-gray-900">{finding.title}</h2>
          <button onClick={onClose} className="text-2xl leading-none text-gray-400 hover:text-gray-600">
            ×
          </button>
        </div>
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <SeverityBadge severity={finding.severity} />
          <ToolBadge label={finding.tool} />
          <ToolBadge label={finding.category} />
          {finding.is_new && (
            <span className="rounded bg-red-100 px-2 py-0.5 text-[11px] font-bold uppercase text-red-700">
              new
            </span>
          )}
        </div>
        <dl className="space-y-3">
          <Field label="Rule" value={finding.rule_id} />
          <Field label="CVE" value={finding.cve} />
          <Field label="CWE" value={finding.cwe} />
          <Field
            label="Location"
            value={
              finding.file_path
                ? `${finding.file_path}${finding.line_start ? `:${finding.line_start}` : ""}`
                : finding.url
            }
          />
          {finding.package_name && (
            <Field
              label="Package"
              value={`${finding.package_name} ${finding.installed_version ?? ""}${
                finding.fixed_version ? ` → fixed in ${finding.fixed_version}` : ""
              }`}
            />
          )}
          {finding.description && (
            <div>
              <dt className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                Description
              </dt>
              <dd className="whitespace-pre-wrap text-sm text-gray-800">{finding.description}</dd>
            </div>
          )}
          {finding.remediation && (
            <div>
              <dt className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                Remediation
              </dt>
              <dd className="whitespace-pre-wrap rounded bg-emerald-50 p-2 text-sm text-emerald-900">
                {finding.remediation}
              </dd>
            </div>
          )}
          {finding.raw && Object.keys(finding.raw).length > 0 && (
            <div>
              <dt className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                Raw tool output
              </dt>
              <dd>
                <pre className="max-h-80 overflow-auto rounded bg-gray-900 p-3 text-[11px] leading-relaxed text-gray-100">
                  {JSON.stringify(finding.raw, null, 2)}
                </pre>
              </dd>
            </div>
          )}
        </dl>
      </div>
    </div>
  );
}
