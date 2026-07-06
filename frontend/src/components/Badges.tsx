import { SEVERITIES, SEVERITY_COLORS, type Severity } from "../api/types";

export function SeverityBadge({ severity }: { severity: Severity | string }) {
  const color = SEVERITY_COLORS[severity as Severity] ?? "#898781";
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-gray-700">
      <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: color }} />
      {severity}
    </span>
  );
}

export function ToolBadge({ label }: { label: string }) {
  return (
    <span className="inline-block rounded bg-gray-100 px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide text-gray-600">
      {label}
    </span>
  );
}

const STATUS_STYLES: Record<string, string> = {
  queued: "bg-gray-100 text-gray-600",
  running: "bg-sky-100 text-sky-700 animate-pulse",
  completed: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
  cancelled: "bg-gray-200 text-gray-500",
};

export function StatusPill({ status }: { status: string }) {
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${
        STATUS_STYLES[status] ?? "bg-gray-100 text-gray-600"
      }`}
    >
      {status}
    </span>
  );
}

/** Compact per-severity counts, e.g. for a table cell. Shows only non-zero severities. */
export function SeverityBreakdown({ counts }: { counts: Record<string, number> | null }) {
  if (!counts) return <span className="text-gray-400">—</span>;
  const active = SEVERITIES.filter((sev) => (counts[sev] ?? 0) > 0);
  if (active.length === 0) return <span className="text-emerald-600">0</span>;
  return (
    <span className="flex flex-wrap gap-x-2.5 gap-y-1">
      {active.map((sev) => (
        <span key={sev} className="flex items-center gap-1 text-xs text-gray-600" title={sev}>
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: SEVERITY_COLORS[sev] }} />
          {counts[sev]}
        </span>
      ))}
    </span>
  );
}
