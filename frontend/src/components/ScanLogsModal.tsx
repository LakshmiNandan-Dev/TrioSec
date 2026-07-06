import { useQuery } from "@tanstack/react-query";
import { getScan, getScanLogs } from "../api/endpoints";
import { StatusPill } from "./Badges";

export default function ScanLogsModal({
  scanId,
  onClose,
}: {
  scanId: number;
  onClose: () => void;
}) {
  const { data: scan } = useQuery({ queryKey: ["scan", scanId], queryFn: () => getScan(scanId) });
  const running = scan?.status === "queued" || scan?.status === "running";

  const { data: logs, isLoading } = useQuery({
    queryKey: ["scan-logs", scanId],
    queryFn: () => getScanLogs(scanId),
    // Keep streaming while the scan is still active.
    refetchInterval: running ? 2000 : false,
  });

  return (
    <div className="fixed inset-0 z-40" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="absolute right-0 top-0 flex h-full w-full max-w-2xl flex-col bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-gray-200 p-4">
          <h2 className="flex items-center gap-3 text-base font-bold text-gray-900">
            Scan #{scanId} logs
            {scan && <StatusPill status={scan.status} />}
          </h2>
          <button onClick={onClose} className="text-2xl leading-none text-gray-400 hover:text-gray-600">
            ×
          </button>
        </div>
        <pre className="flex-1 overflow-auto bg-gray-900 p-4 text-xs leading-relaxed text-gray-100">
          {isLoading ? "Loading logs…" : logs || "No logs yet."}
        </pre>
        {running && (
          <div className="border-t border-gray-200 p-2 text-center text-xs text-gray-400">
            Live — refreshing while the scan runs
          </div>
        )}
      </div>
    </div>
  );
}
