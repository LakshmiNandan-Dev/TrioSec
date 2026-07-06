import { useMutation, useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { apiErrorMessage } from "../api/client";
import { createScan, getSettings } from "../api/endpoints";

const inputClass =
  "w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none";

export default function NewScanPage() {
  const { projectId } = useParams();
  const id = Number(projectId);
  const navigate = useNavigate();

  const [types, setTypes] = useState<string[]>(["sast", "sca"]);
  const [targetType, setTargetType] = useState<"local_path" | "git_url">("local_path");
  const [targetValue, setTargetValue] = useState("");
  const [dastUrl, setDastUrl] = useState("");
  const [fullScan, setFullScan] = useState(false);
  const [authorized, setAuthorized] = useState(false);
  const [error, setError] = useState("");

  const needsCode = types.includes("sast") || types.includes("sca") || types.includes("iac");
  const needsDast = types.includes("dast");

  const { data: settings } = useQuery({ queryKey: ["settings"], queryFn: getSettings });
  const allowlist = (settings?.dast_allowed_domains ?? "")
    .split(/[\s,]+/)
    .map((d) => d.trim())
    .filter(Boolean);

  const toggleType = (t: string) =>
    setTypes((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));

  const mutation = useMutation({
    mutationFn: () =>
      createScan({
        project_id: id,
        scan_types: types,
        target_type: needsCode ? targetType : null,
        target_value: needsCode ? targetValue : null,
        dast_url: needsDast ? dastUrl : null,
        dast_full_scan: fullScan,
        authorization_acknowledged: needsDast ? authorized : false,
      }),
    onSuccess: (scan) => navigate(`/scans/${scan.id}`),
    onError: (err) => setError(apiErrorMessage(err)),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError("");
    mutation.mutate();
  };

  return (
    <div className="max-w-2xl">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">New scan</h1>
      <form onSubmit={onSubmit} className="space-y-6 rounded-lg border border-gray-200 bg-white p-6">
        <div>
          <h3 className="mb-2 text-sm font-semibold text-gray-700">Scan types</h3>
          <div className="space-y-2">
            {[
              ["sast", "SAST — static code analysis (Semgrep)"],
              ["sca", "SCA — vulnerable dependencies & secrets (Trivy)"],
              ["iac", "IaC — infrastructure misconfigurations: Terraform, K8s, Dockerfile (Trivy)"],
              ["dast", "DAST — running application scan (OWASP ZAP)"],
            ].map(([value, label]) => (
              <label key={value} className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={types.includes(value)}
                  onChange={() => toggleType(value)}
                />
                {label}
              </label>
            ))}
          </div>
        </div>

        {needsCode && (
          <div>
            <h3 className="mb-2 text-sm font-semibold text-gray-700">Code target</h3>
            <div className="mb-2 flex gap-4 text-sm text-gray-700">
              <label className="flex items-center gap-1.5">
                <input
                  type="radio"
                  checked={targetType === "local_path"}
                  onChange={() => setTargetType("local_path")}
                />
                Local path (inside WORKSPACE_ROOT)
              </label>
              <label className="flex items-center gap-1.5">
                <input
                  type="radio"
                  checked={targetType === "git_url"}
                  onChange={() => setTargetType("git_url")}
                />
                Git URL
              </label>
            </div>
            <input
              value={targetValue}
              onChange={(e) => setTargetValue(e.target.value)}
              placeholder={
                targetType === "local_path"
                  ? "e.g. my-app  (relative to WORKSPACE_ROOT)"
                  : "e.g. https://github.com/org/repo.git"
              }
              className={inputClass}
            />
          </div>
        )}

        {needsDast && (
          <div>
            <h3 className="mb-2 text-sm font-semibold text-gray-700">Running app target (DAST)</h3>
            <input
              value={dastUrl}
              onChange={(e) => setDastUrl(e.target.value)}
              placeholder="e.g. http://host.docker.internal:3000"
              className={inputClass}
            />
            <p className="mt-1 text-xs text-gray-400">
              For apps running on this machine use http://host.docker.internal:&lt;port&gt; —
              "localhost" would point at the scanner container itself.
            </p>
            <label className="mt-2 flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={fullScan}
                onChange={(e) => setFullScan(e.target.checked)}
              />
              Full active scan (slower and intrusive — only against apps you own)
            </label>

            <div className="mt-4 rounded-md border border-amber-300 bg-amber-50 p-3">
              {allowlist.length > 0 && (
                <p className="mb-2 text-xs text-amber-800">
                  <span className="font-semibold">Approved DAST domains:</span>{" "}
                  {allowlist.join(", ")}. Targets outside this list are rejected.
                </p>
              )}
              <label className="flex items-start gap-2 text-sm text-amber-900">
                <input
                  type="checkbox"
                  className="mt-0.5"
                  checked={authorized}
                  onChange={(e) => setAuthorized(e.target.checked)}
                />
                <span>
                  I confirm I own this target, or have explicit written permission to test it.
                  Scanning systems without authorization may be illegal.
                </span>
              </label>
            </div>
          </div>
        )}

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={mutation.isPending || types.length === 0 || (needsDast && !authorized)}
          className="rounded-md bg-sky-600 px-5 py-2 text-sm font-semibold text-white hover:bg-sky-700 disabled:opacity-50"
        >
          {mutation.isPending ? "Starting…" : "Start scan"}
        </button>
      </form>
    </div>
  );
}
