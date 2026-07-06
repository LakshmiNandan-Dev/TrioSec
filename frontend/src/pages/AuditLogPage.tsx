import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { listAudit } from "../api/endpoints";
import type { AuditEvent } from "../api/types";

const PAGE_SIZE = 50;

const ACTIONS = [
  "login.success",
  "login.failure",
  "password.change",
  "scan.create",
  "user.create",
  "user.update",
  "user.delete",
  "settings.update",
  "report.email",
];

const ACTION_STYLE: Record<string, string> = {
  "login.failure": "bg-red-100 text-red-700",
  "login.success": "bg-emerald-100 text-emerald-700",
  "user.delete": "bg-red-100 text-red-700",
  "user.create": "bg-sky-100 text-sky-700",
  "scan.create": "bg-gray-100 text-gray-600",
};

function detailText(e: AuditEvent): string {
  if (!e.detail) return "";
  return Object.entries(e.detail)
    .filter(([, v]) => v !== null && v !== undefined)
    .map(([k, v]) => `${k}=${Array.isArray(v) ? v.join("/") : v}`)
    .join("  ");
}

export default function AuditLogPage() {
  const [action, setAction] = useState("");
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);

  const filters = {
    action: action || undefined,
    q: q || undefined,
    page,
    page_size: PAGE_SIZE,
  };

  const { data } = useQuery({
    queryKey: ["audit", filters],
    queryFn: () => listAudit(filters),
    placeholderData: keepPreviousData,
    refetchInterval: 15_000,
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold text-gray-900">Audit log</h1>
      <p className="mb-6 text-sm text-gray-500">
        Security-relevant events — who did what, from which IP. Append-only.
      </p>

      <div className="rounded-lg border border-gray-200 bg-white">
        <div className="flex flex-wrap items-center gap-2 border-b border-gray-200 p-3">
          <select
            value={action}
            onChange={(e) => {
              setAction(e.target.value);
              setPage(1);
            }}
            className="rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm text-gray-700"
          >
            <option value="">All actions</option>
            {ACTIONS.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
          <input
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1);
            }}
            placeholder="Search actor, target, IP…"
            className="min-w-56 flex-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-sky-500 focus:outline-none"
          />
          <span className="text-sm text-gray-500">{data?.total ?? 0} events</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-[11px] uppercase tracking-wider text-gray-400">
                <th className="px-4 py-2 font-semibold">Time</th>
                <th className="px-4 py-2 font-semibold">Actor</th>
                <th className="px-4 py-2 font-semibold">Action</th>
                <th className="px-4 py-2 font-semibold">Target</th>
                <th className="px-4 py-2 font-semibold">IP</th>
                <th className="px-4 py-2 font-semibold">Detail</th>
              </tr>
            </thead>
            <tbody>
              {(data?.items ?? []).map((e) => (
                <tr key={e.id} className="border-b border-gray-100 last:border-0">
                  <td className="whitespace-nowrap px-4 py-2 text-gray-500">
                    {new Date(e.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-2 text-gray-800">{e.actor_email ?? "—"}</td>
                  <td className="px-4 py-2">
                    <span
                      className={`rounded px-2 py-0.5 text-xs font-medium ${
                        ACTION_STYLE[e.action] ?? "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {e.action}
                    </span>
                  </td>
                  <td className="max-w-xs truncate px-4 py-2 text-gray-600">{e.target ?? "—"}</td>
                  <td className="whitespace-nowrap px-4 py-2 font-mono text-xs text-gray-500">
                    {e.ip ?? "—"}
                  </td>
                  <td className="px-4 py-2 font-mono text-[11px] text-gray-400">{detailText(e)}</td>
                </tr>
              ))}
              {data && data.items.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-sm text-gray-400">
                    No events match the current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

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
      </div>
    </div>
  );
}
