import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { listFindings } from "../api/endpoints";
import { SEVERITIES, type Finding } from "../api/types";
import { SeverityBadge, ToolBadge } from "./Badges";
import FindingDetailDrawer from "./FindingDetailDrawer";

const PAGE_SIZE = 50;

const selectClass =
  "rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm text-gray-700 focus:border-sky-500 focus:outline-none";

export default function FindingsTable({ scanId }: { scanId: number }) {
  const [severity, setSeverity] = useState("");
  const [tool, setTool] = useState("");
  const [category, setCategory] = useState("");
  const [onlyNew, setOnlyNew] = useState(false);
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Finding | null>(null);

  const filters = {
    severity: severity || undefined,
    tool: tool || undefined,
    category: category || undefined,
    is_new: onlyNew ? true : undefined,
    q: q || undefined,
    page,
    page_size: PAGE_SIZE,
  };

  const { data, isLoading } = useQuery({
    queryKey: ["findings", scanId, filters],
    queryFn: () => listFindings(scanId, filters),
    placeholderData: keepPreviousData,
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  const resetPage = () => setPage(1);

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <div className="flex flex-wrap items-center gap-2 border-b border-gray-200 p-3">
        <select
          value={severity}
          onChange={(e) => {
            setSeverity(e.target.value);
            resetPage();
          }}
          className={selectClass}
        >
          <option value="">All severities</option>
          {SEVERITIES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={tool}
          onChange={(e) => {
            setTool(e.target.value);
            resetPage();
          }}
          className={selectClass}
        >
          <option value="">All tools</option>
          <option value="semgrep">semgrep</option>
          <option value="trivy">trivy</option>
          <option value="zap">zap</option>
        </select>
        <select
          value={category}
          onChange={(e) => {
            setCategory(e.target.value);
            resetPage();
          }}
          className={selectClass}
        >
          <option value="">All categories</option>
          <option value="sast">sast</option>
          <option value="sca">sca</option>
          <option value="secret">secret</option>
          <option value="iac">iac</option>
          <option value="dast">dast</option>
        </select>
        <label className="flex items-center gap-1.5 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={onlyNew}
            onChange={(e) => {
              setOnlyNew(e.target.checked);
              resetPage();
            }}
          />
          Only new
        </label>
        <input
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            resetPage();
          }}
          placeholder="Search title, file, package, CVE…"
          className="min-w-56 flex-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-sky-500 focus:outline-none"
        />
        <span className="text-sm text-gray-500">{data?.total ?? 0} findings</span>
      </div>

      {isLoading ? (
        <p className="p-6 text-sm text-gray-400">Loading findings…</p>
      ) : data && data.items.length > 0 ? (
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-[11px] uppercase tracking-wider text-gray-400">
              <th className="px-4 py-2 font-semibold">Severity</th>
              <th className="px-4 py-2 font-semibold">Finding</th>
              <th className="px-4 py-2 font-semibold">Location</th>
              <th className="px-4 py-2 font-semibold">Tool</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((f) => (
              <tr
                key={f.id}
                onClick={() => setSelected(f)}
                className="cursor-pointer border-b border-gray-100 last:border-0 hover:bg-sky-50"
              >
                <td className="px-4 py-2.5">
                  <SeverityBadge severity={f.severity} />
                </td>
                <td className="max-w-md px-4 py-2.5">
                  <div className="truncate font-medium text-gray-900">{f.title}</div>
                  <div className="flex gap-2 text-[11px] text-gray-400">
                    {f.cve && <span>{f.cve}</span>}
                    {f.cwe && <span>{f.cwe}</span>}
                    {f.is_new && <span className="font-bold text-red-600">NEW</span>}
                  </div>
                </td>
                <td className="max-w-xs truncate px-4 py-2.5 font-mono text-xs text-gray-500">
                  {f.file_path
                    ? `${f.file_path}${f.line_start ? `:${f.line_start}` : ""}`
                    : (f.url ?? f.package_name ?? "—")}
                </td>
                <td className="px-4 py-2.5">
                  <ToolBadge label={f.tool} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="p-6 text-sm text-gray-400">No findings match the current filters.</p>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-gray-200 p-3 text-sm">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="rounded-md border border-gray-300 px-3 py-1 disabled:opacity-40"
          >
            Previous
          </button>
          <span className="text-gray-500">
            Page {page} of {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="rounded-md border border-gray-300 px-3 py-1 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}

      {selected && <FindingDetailDrawer finding={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
