import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { apiErrorMessage } from "../api/client";
import { changePassword } from "../api/endpoints";

const inputClass =
  "w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none";

export default function ChangePasswordModal({ onClose }: { onClose: () => void }) {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [msg, setMsg] = useState("");

  const mutation = useMutation({
    mutationFn: () => changePassword(current, next),
    onSuccess: () => {
      setMsg("Password changed.");
      setCurrent("");
      setNext("");
    },
    onError: (err) => setMsg(apiErrorMessage(err)),
  });

  const submit = (e: FormEvent) => {
    e.preventDefault();
    setMsg("");
    mutation.mutate();
  };

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <form onSubmit={submit} className="relative w-full max-w-sm rounded-xl bg-white p-6 shadow-2xl">
        <h2 className="mb-4 text-base font-bold text-gray-900">Change password</h2>
        <label className="mb-1 block text-xs font-medium text-gray-500">Current password</label>
        <input
          type="password"
          value={current}
          onChange={(e) => setCurrent(e.target.value)}
          required
          className={`${inputClass} mb-3`}
        />
        <label className="mb-1 block text-xs font-medium text-gray-500">
          New password (min 8 characters)
        </label>
        <input
          type="password"
          value={next}
          onChange={(e) => setNext(e.target.value)}
          required
          minLength={8}
          className={`${inputClass} mb-4`}
        />
        {msg && (
          <p className={`mb-3 text-sm ${msg === "Password changed." ? "text-emerald-700" : "text-red-600"}`}>
            {msg}
          </p>
        )}
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
          >
            Close
          </button>
          <button
            type="submit"
            disabled={mutation.isPending}
            className="rounded-md bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700 disabled:opacity-50"
          >
            {mutation.isPending ? "Saving…" : "Change password"}
          </button>
        </div>
      </form>
    </div>
  );
}
