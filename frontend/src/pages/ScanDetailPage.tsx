import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { apiErrorMessage } from "../api/client";
import { cancelScan, downloadReport, emailReport, getScan, getScanLogs } from "../api/endpoints";
import { StatusPill } from "../components/Badges";
import FindingsTable from "../components/FindingsTable";
import ScanProgress from "../components/ScanProgress";
import SeverityTiles from "../components/SeverityTiles";
import { useRerunScan } from "../hooks/useRerunScan";

export default function ScanDetailPage() {
  const { scanId } = useParams();
  const id = Number(scanId);
  const queryClient = useQueryClient();
  const [showEmail, setShowEmail] = useState(false);
  const [recipient, setRecipient] = useState("");
  const [emailStatus, setEmailStatus] = useState("");
  const [showLogs, setShowLogs] = useState(false);

  const { data: scan } = useQuery({
    queryKey: ["scan", id],
    queryFn: () => getScan(id),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "queued" || status === "running" ? 2000 : false;
    },
  });

  const { data: logs } = useQuery({
    queryKey: ["scan-logs", id],
    queryFn: () => getScanLogs(id),
    enabled: showLogs,
  });

  const cancel = useMutation({
    mutationFn: () => cancelScan(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["scan", id] }),
  });

  const email = useMutation({
    mutationFn: () => emailReport(id, recipient),
    onSuccess: () => setEmailStatus(`Report sent to ${recipient}`),
    onError: (err) => setEmailStatus(`Failed: ${apiErrorMessage(err)}`),
  });

  const rerun = useRerunScan();

  if (!scan) return <p className="text-sm text-gray-400">Loading scan…</p>;

  const running = scan.status === "queued" || scan.status === "running";
  const finished = scan.status === "completed" || scan.status === "failed";

  const sendEmail = (e: FormEvent) => {
    e.preventDefault();
    setEmailStatus("");
    email.mutate();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="flex items-center gap-3 text-2xl font-bold text-gray-900">
            Scan #{scan.id} <StatusPill status={scan.status} />
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            <Link to={`/projects/${scan.project_id}`} className="text-sky-700 hover:underline">
              ← back to project
            </Link>
            <span className="mx-2">·</span>
            {scan.target_value && <span className="font-mono">{scan.target_value}</span>}
            {scan.dast_url && <span className="ml-2 font-mono">{scan.dast_url}</span>}
          </p>
          {scan.authorized_by && (
            <p className="mt-0.5 text-xs text-gray-400">
              DAST authorized by {scan.authorized_by}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          {running ? (
            <button
              onClick={() => cancel.mutate()}
              className="rounded-md border border-red-300 px-3 py-2 text-sm font-semibold text-red-700 hover:bg-red-50"
            >
              Cancel scan
            </button>
          ) : (
            <button
              onClick={() => rerun.mutate(scan)}
              disabled={rerun.isPending}
              title="Run this scan again with the same target — e.g. after code changes"
              className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              {rerun.isPending ? "Starting…" : "↻ Re-run scan"}
            </button>
          )}
          {finished && (
            <>
              <button
                onClick={() => downloadReport(id, "json")}
                className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                JSON
              </button>
              <button
                onClick={() => downloadReport(id, "html")}
                className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                HTML
              </button>
              <button
                onClick={() => downloadReport(id, "pdf")}
                className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                PDF
              </button>
              <button
                onClick={() => setShowEmail((v) => !v)}
                className="rounded-md bg-sky-600 px-3 py-2 text-sm font-semibold text-white hover:bg-sky-700"
              >
                Email report
              </button>
            </>
          )}
        </div>
      </div>

      {showEmail && finished && (
        <form
          onSubmit={sendEmail}
          className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-4"
        >
          <input
            type="email"
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            placeholder="recipient@example.com"
            required
            className="w-72 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={email.isPending}
            className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {email.isPending ? "Sending…" : "Send PDF report"}
          </button>
          {emailStatus && (
            <span
              className={`text-sm ${emailStatus.startsWith("Failed") ? "text-red-600" : "text-emerald-700"}`}
            >
              {emailStatus}
            </span>
          )}
        </form>
      )}

      {running ? (
        <ScanProgress scan={scan} />
      ) : (
        <>
          <SeverityTiles counts={scan.severity_counts} />
          {scan.error_message && (
            <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{scan.error_message}</p>
          )}
          <FindingsTable scanId={id} />
        </>
      )}

      <div>
        <button
          onClick={() => setShowLogs((v) => !v)}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          {showLogs ? "Hide scan logs" : "Show scan logs"}
        </button>
        {showLogs && (
          <pre className="mt-2 max-h-72 overflow-auto rounded-lg bg-gray-900 p-4 text-xs leading-relaxed text-gray-100">
            {logs || "No logs yet."}
          </pre>
        )}
      </div>
    </div>
  );
}
