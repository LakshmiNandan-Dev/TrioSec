import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { apiErrorMessage } from "../api/client";
import { createScan } from "../api/endpoints";
import type { Scan } from "../api/types";

/**
 * Re-run a scan: clone its configuration (types + target) into a fresh scan and
 * navigate to it. Each run stays a separate immutable snapshot so trends/compare
 * keep working — this is "scan again after code changes", not "resume".
 */
export function useRerunScan() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (scan: Scan) =>
      createScan({
        project_id: scan.project_id,
        scan_types: scan.scan_types,
        target_type: scan.target_type,
        target_value: scan.target_value,
        dast_url: scan.dast_url,
        dast_full_scan: scan.dast_full_scan,
        // The original run was already authorized for this same target; re-run inherits it.
        // The domain allowlist is still re-checked server-side on every create.
        authorization_acknowledged: scan.scan_types.includes("dast"),
      }),
    onSuccess: (newScan) => {
      queryClient.invalidateQueries({ queryKey: ["scans", newScan.project_id] });
      navigate(`/scans/${newScan.id}`);
    },
    onError: (err) => alert(`Could not start re-run: ${apiErrorMessage(err)}`),
  });
}
