import { SEVERITIES, SEVERITY_COLORS } from "../api/types";

export default function SeverityTiles({ counts }: { counts: Record<string, number> | null }) {
  return (
    <div className="grid grid-cols-5 gap-3">
      {SEVERITIES.map((sev) => (
        <div
          key={sev}
          className="rounded-lg border border-gray-200 bg-white p-3"
          style={{ borderLeft: `4px solid ${SEVERITY_COLORS[sev]}` }}
        >
          <div className="text-2xl font-bold text-gray-900">{counts?.[sev] ?? 0}</div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-gray-500">
            {sev}
          </div>
        </div>
      ))}
    </div>
  );
}
