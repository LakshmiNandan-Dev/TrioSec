import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiErrorMessage } from "../api/client";
import { compareScans, getProject, getTrends, listScans, updateProject } from "../api/endpoints";
import type { FindingBrief, Scan } from "../api/types";
import { SeverityBadge, SeverityBreakdown, StatusPill } from "../components/Badges";
import ScanLogsModal from "../components/ScanLogsModal";
import SeverityTiles from "../components/SeverityTiles";
import TrendChart from "../components/TrendChart";
import { useRerunScan } from "../hooks/useRerunScan";

const isActive = (s: Scan) => s.status === "queued" || s.status === "running";

function CompareList({ title, items, tone }: { title: string; items: FindingBrief[]; tone: string }) {
  return (
    <div className="flex-1 rounded-lg border border-gray-200 bg-white p-4">
      <h4 className={`mb-2 text-sm font-bold ${tone}`}>
        {title} ({items.length})
      </h4>
      {items.length === 0 ? (
        <p className="text-sm text-gray-400">None</p>
      ) : (
        <ul className="max-h-64 space-y-1.5 overflow-y-auto">
          {items.map((f) => (
            <li key={f.id} className="flex items-center gap-2 text-sm text-gray-700">
              <SeverityBadge severity={f.severity} />
              <span className="truncate">{f.title}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function ProjectDetailPage() {
  const { projectId } = useParams();
  const id = Number(projectId);
  const [baseId, setBaseId] = useState<number | "">("");
  const [headId, setHeadId] = useState<number | "">("");
  const [logsScanId, setLogsScanId] = useState<number | null>(null);
  const [gitToken, setGitToken] = useState("");
  const rerun = useRerunScan();
  const queryClient = useQueryClient();

  const saveToken = useMutation({
    mutationFn: (data: { git_token?: string; clear_git_token?: boolean }) =>
      updateProject(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", id] });
      setGitToken("");
    },
    onError: (err) => alert(apiErrorMessage(err)),
  });

  const { data: project } = useQuery({ queryKey: ["project", id], queryFn: () => getProject(id) });
  const { data: scans } = useQuery({
    queryKey: ["scans", id],
    queryFn: () => listScans(id),
    refetchInterval: (query) =>
      query.state.data?.some((s) => s.status === "queued" || s.status === "running") ? 3000 : false,
  });
  const { data: trends } = useQuery({ queryKey: ["trends", id], queryFn: () => getTrends(id) });
  const { data: comparison } = useQuery({
    queryKey: ["compare", id, baseId, headId],
    queryFn: () => compareScans(id, baseId as number, headId as number),
    enabled: baseId !== "" && headId !== "" && baseId !== headId,
  });

  const allScans = scans ?? [];
  const completed = allScans.filter((s) => s.status === "completed");
  const latest = allScans[0];
  const runningCount = allScans.filter(isActive).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{project?.name ?? "…"}</h1>
          {project?.description && <p className="text-sm text-gray-500">{project.description}</p>}
        </div>
        <Link
          to={`/projects/${id}/new-scan`}
          className="rounded-md bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700"
        >
          New scan
        </Link>
      </div>

      {allScans.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-lg border border-gray-200 bg-white p-3">
            <div className="text-2xl font-bold text-gray-900">{allScans.length}</div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-gray-500">
              Total scans
            </div>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-3">
            <div className="text-2xl font-bold text-gray-900">
              {latest?.status === "completed" ? latest.total_findings : "—"}
            </div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-gray-500">
              Latest findings
            </div>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-3">
            <div
              className={`text-2xl font-bold ${runningCount > 0 ? "text-sky-600" : "text-gray-900"}`}
            >
              {runningCount > 0 ? runningCount : "Idle"}
            </div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-gray-500">
              {runningCount > 0 ? "Scanning now" : "No active scans"}
            </div>
          </div>
        </div>
      )}

      {latest && (
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-700">
              Latest scan ·{" "}
              <Link to={`/scans/${latest.id}`} className="text-sky-700 hover:underline">
                #{latest.id}
              </Link>
              <span className="ml-2 font-normal text-gray-400">
                {new Date(latest.created_at).toLocaleString()}
              </span>
            </h3>
            <div className="flex items-center gap-2">
              <StatusPill status={latest.status} />
              <button
                onClick={() => setLogsScanId(latest.id)}
                className="rounded-md border border-gray-300 px-2.5 py-1 text-xs font-medium text-gray-600 hover:bg-gray-50"
              >
                View logs
              </button>
            </div>
          </div>
          {isActive(latest) ? (
            <div className="flex flex-wrap gap-2">
              {latest.scan_types.map((t) => (
                <span
                  key={t}
                  className="flex items-center gap-1.5 rounded bg-gray-50 px-2.5 py-1 text-xs"
                >
                  <span className="font-medium uppercase text-gray-600">{t}</span>
                  <StatusPill status={latest.tool_status?.[t] ?? "queued"} />
                </span>
              ))}
            </div>
          ) : (
            <>
              <SeverityTiles counts={latest.severity_counts} />
              <p className="mt-2 text-xs text-gray-400">
                {latest.total_findings} findings · {latest.scan_types.join(", ").toUpperCase()}
                {latest.finished_at
                  ? ` · finished ${new Date(latest.finished_at).toLocaleString()}`
                  : ""}
              </p>
              {latest.error_message && (
                <p className="mt-2 rounded bg-red-50 p-2 text-xs text-red-700">
                  {latest.error_message}
                </p>
              )}
            </>
          )}
        </div>
      )}

      <TrendChart points={trends ?? []} />

      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-700">Private repository access</h3>
          <span className={`text-xs ${project?.has_git_token ? "text-emerald-600" : "text-gray-400"}`}>
            {project?.has_git_token ? "● Git token configured" : "○ No token (public repos only)"}
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="password"
            value={gitToken}
            onChange={(e) => setGitToken(e.target.value)}
            placeholder={project?.has_git_token ? "Enter a new token to replace" : "Git access token (PAT)"}
            autoComplete="new-password"
            className="min-w-64 flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none"
          />
          <button
            onClick={() => saveToken.mutate({ git_token: gitToken })}
            disabled={!gitToken || saveToken.isPending}
            className="rounded-md bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700 disabled:opacity-50"
          >
            {project?.has_git_token ? "Replace" : "Save token"}
          </button>
          {project?.has_git_token && (
            <button
              onClick={() => {
                if (confirm("Remove the stored git token for this project?")) {
                  saveToken.mutate({ clear_git_token: true });
                }
              }}
              className="rounded-md border border-red-300 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50"
            >
              Remove
            </button>
          )}
        </div>
        <p className="mt-1 text-xs text-gray-400">
          A read-only Personal Access Token, stored encrypted. Used only to clone private repos for
          this project's Git-URL scans.
        </p>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white">
        <h3 className="border-b border-gray-200 px-4 py-3 text-sm font-semibold text-gray-700">
          Scan history
        </h3>
        {scans && scans.length > 0 ? (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-[11px] uppercase tracking-wider text-gray-400">
                <th className="px-4 py-2 font-semibold">Scan</th>
                <th className="px-4 py-2 font-semibold">Started</th>
                <th className="px-4 py-2 font-semibold">Types</th>
                <th className="px-4 py-2 font-semibold">Status</th>
                <th className="px-4 py-2 font-semibold">Findings</th>
                <th className="px-4 py-2 font-semibold"></th>
              </tr>
            </thead>
            <tbody>
              {scans.map((s) => (
                <tr key={s.id} className="border-b border-gray-100 last:border-0 hover:bg-sky-50">
                  <td className="px-4 py-2.5">
                    <Link to={`/scans/${s.id}`} className="font-medium text-sky-700 hover:underline">
                      #{s.id}
                    </Link>
                  </td>
                  <td className="px-4 py-2.5 text-gray-500">
                    {new Date(s.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-2.5 uppercase text-gray-600">{s.scan_types.join(", ")}</td>
                  <td className="px-4 py-2.5">
                    <StatusPill status={s.status} />
                  </td>
                  <td className="px-4 py-2.5 text-gray-700">
                    {isActive(s) ? (
                      <span className="text-sky-600">scanning…</span>
                    ) : (
                      <SeverityBreakdown counts={s.severity_counts} />
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => setLogsScanId(s.id)}
                        className="rounded-md border border-gray-300 px-2.5 py-1 text-xs font-medium text-gray-600 hover:bg-gray-50"
                      >
                        Logs
                      </button>
                      {!isActive(s) && (
                        <button
                          onClick={() => rerun.mutate(s)}
                          disabled={rerun.isPending}
                          title="Run this scan again with the same target"
                          className="rounded-md border border-emerald-300 px-2.5 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-50 disabled:opacity-50"
                        >
                          ↻ Re-run
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="p-6 text-sm text-gray-400">No scans yet.</p>
        )}
      </div>

      {completed.length >= 2 && (
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-semibold text-gray-700">Compare two runs</h3>
          <div className="mb-4 flex items-center gap-3 text-sm">
            <select
              value={baseId}
              onChange={(e) => setBaseId(e.target.value ? Number(e.target.value) : "")}
              className="rounded-md border border-gray-300 px-2 py-1.5"
            >
              <option value="">Baseline scan…</option>
              {completed.map((s) => (
                <option key={s.id} value={s.id}>
                  #{s.id} — {new Date(s.created_at).toLocaleString()}
                </option>
              ))}
            </select>
            <span className="text-gray-400">vs</span>
            <select
              value={headId}
              onChange={(e) => setHeadId(e.target.value ? Number(e.target.value) : "")}
              className="rounded-md border border-gray-300 px-2 py-1.5"
            >
              <option value="">Newer scan…</option>
              {completed.map((s) => (
                <option key={s.id} value={s.id}>
                  #{s.id} — {new Date(s.created_at).toLocaleString()}
                </option>
              ))}
            </select>
          </div>
          {comparison && (
            <div className="flex gap-4">
              <CompareList title="Added" items={comparison.added} tone="text-red-700" />
              <CompareList title="Fixed" items={comparison.fixed} tone="text-emerald-700" />
              <div className="flex w-40 flex-col items-center justify-center rounded-lg border border-gray-200 bg-gray-50 p-4">
                <span className="text-2xl font-bold text-gray-700">{comparison.unchanged_count}</span>
                <span className="text-xs uppercase tracking-wider text-gray-400">unchanged</span>
              </div>
            </div>
          )}
        </div>
      )}

      {logsScanId !== null && (
        <ScanLogsModal scanId={logsScanId} onClose={() => setLogsScanId(null)} />
      )}
    </div>
  );
}
