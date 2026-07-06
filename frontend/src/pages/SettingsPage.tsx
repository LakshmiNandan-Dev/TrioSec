import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type FormEvent } from "react";
import { apiErrorMessage } from "../api/client";
import { getSettings, testSmtp, updateSettings } from "../api/endpoints";

const inputClass =
  "w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { data: settings } = useQuery({ queryKey: ["settings"], queryFn: getSettings });

  const [form, setForm] = useState({
    smtp_host: "",
    smtp_port: 587,
    smtp_username: "",
    smtp_password: "",
    smtp_use_tls: true,
    smtp_from_address: "",
    default_semgrep_config: "p/default",
    dast_allowed_domains: "",
  });
  const [status, setStatus] = useState("");
  const [testRecipient, setTestRecipient] = useState("");

  useEffect(() => {
    if (settings) {
      setForm((prev) => ({
        ...prev,
        smtp_host: settings.smtp_host ?? "",
        smtp_port: settings.smtp_port,
        smtp_username: settings.smtp_username ?? "",
        smtp_use_tls: settings.smtp_use_tls,
        smtp_from_address: settings.smtp_from_address ?? "",
        default_semgrep_config: settings.default_semgrep_config,
        dast_allowed_domains: settings.dast_allowed_domains ?? "",
      }));
    }
  }, [settings]);

  const save = useMutation({
    mutationFn: () =>
      updateSettings({
        ...form,
        smtp_password: form.smtp_password || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      setForm((prev) => ({ ...prev, smtp_password: "" }));
      setStatus("Settings saved.");
    },
    onError: (err) => setStatus(`Save failed: ${apiErrorMessage(err)}`),
  });

  const test = useMutation({
    mutationFn: () => testSmtp(testRecipient),
    onSuccess: () => setStatus(`Test email sent to ${testRecipient}.`),
    onError: (err) => setStatus(`SMTP test failed: ${apiErrorMessage(err)}`),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setStatus("");
    save.mutate();
  };

  return (
    <div className="max-w-2xl">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Settings</h1>

      <form onSubmit={onSubmit} className="space-y-4 rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="text-sm font-semibold text-gray-700">Email (SMTP) — used to send reports</h3>
        <div className="grid grid-cols-3 gap-3">
          <div className="col-span-2">
            <label className="mb-1 block text-xs font-medium text-gray-500">Host</label>
            <input
              value={form.smtp_host}
              onChange={(e) => setForm({ ...form, smtp_host: e.target.value })}
              placeholder="smtp.example.com (or mailpit for local testing)"
              className={inputClass}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500">Port</label>
            <input
              type="number"
              value={form.smtp_port}
              onChange={(e) => setForm({ ...form, smtp_port: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500">Username</label>
            <input
              value={form.smtp_username}
              onChange={(e) => setForm({ ...form, smtp_username: e.target.value })}
              className={inputClass}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500">
              Password {settings?.has_smtp_password && "(saved — leave blank to keep)"}
            </label>
            <input
              type="password"
              value={form.smtp_password}
              onChange={(e) => setForm({ ...form, smtp_password: e.target.value })}
              placeholder={settings?.has_smtp_password ? "••••••••" : ""}
              className={inputClass}
            />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500">From address</label>
            <input
              value={form.smtp_from_address}
              onChange={(e) => setForm({ ...form, smtp_from_address: e.target.value })}
              placeholder="triosec@example.com"
              className={inputClass}
            />
          </div>
          <label className="mt-5 flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={form.smtp_use_tls}
              onChange={(e) => setForm({ ...form, smtp_use_tls: e.target.checked })}
            />
            Use STARTTLS
          </label>
        </div>

        <h3 className="pt-2 text-sm font-semibold text-gray-700">Scanners</h3>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500">
            Semgrep ruleset (e.g. p/default, p/security-audit, p/owasp-top-ten)
          </label>
          <input
            value={form.default_semgrep_config}
            onChange={(e) => setForm({ ...form, default_semgrep_config: e.target.value })}
            className={inputClass}
          />
        </div>

        <h3 className="pt-2 text-sm font-semibold text-gray-700">DAST authorization</h3>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500">
            Approved DAST domains (one per line or comma-separated). Leave empty to allow any
            target. When set, DAST scans are only permitted against these hosts and their
            subdomains.
          </label>
          <textarea
            value={form.dast_allowed_domains}
            onChange={(e) => setForm({ ...form, dast_allowed_domains: e.target.value })}
            rows={3}
            placeholder={"example.com\nstaging.internal\nhost.docker.internal"}
            className={`${inputClass} font-mono`}
          />
        </div>

        <div className="flex items-center gap-3 pt-2">
          <button
            type="submit"
            disabled={save.isPending}
            className="rounded-md bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700 disabled:opacity-50"
          >
            Save settings
          </button>
          {status && (
            <span
              className={`text-sm ${status.includes("failed") ? "text-red-600" : "text-emerald-700"}`}
            >
              {status}
            </span>
          )}
        </div>
      </form>

      <div className="mt-4 flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-4">
        <input
          type="email"
          value={testRecipient}
          onChange={(e) => setTestRecipient(e.target.value)}
          placeholder="Send a test email to…"
          className="w-72 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none"
        />
        <button
          onClick={() => {
            setStatus("");
            test.mutate();
          }}
          disabled={test.isPending || !testRecipient}
          className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          {test.isPending ? "Sending…" : "Test SMTP"}
        </button>
      </div>
    </div>
  );
}
