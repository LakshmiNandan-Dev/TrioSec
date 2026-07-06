import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { apiErrorMessage } from "../api/client";
import { createUser, deleteUser, listUsers, updateUser } from "../api/endpoints";
import type { User } from "../api/types";
import { useMe } from "../auth/useMe";

const inputClass =
  "rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none";

export default function UsersPage() {
  const queryClient = useQueryClient();
  const { data: me } = useMe();
  const { data: users } = useQuery({ queryKey: ["users"], queryFn: listUsers });

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [error, setError] = useState("");

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["users"] });

  const create = useMutation({
    mutationFn: () => createUser(email, password, isAdmin),
    onSuccess: () => {
      invalidate();
      setEmail("");
      setPassword("");
      setIsAdmin(false);
      setError("");
    },
    onError: (err) => setError(apiErrorMessage(err)),
  });

  const update = useMutation({
    mutationFn: (args: { id: number; data: Partial<Pick<User, "is_admin" | "is_active">> }) =>
      updateUser(args.id, args.data),
    onSuccess: invalidate,
    onError: (err) => alert(apiErrorMessage(err)),
  });

  const remove = useMutation({
    mutationFn: deleteUser,
    onSuccess: invalidate,
    onError: (err) => alert(apiErrorMessage(err)),
  });

  const resetPassword = (u: User) => {
    const pw = prompt(`Set a new password for ${u.email} (min 8 characters):`);
    if (pw && pw.length >= 8) updateUser(u.id, { password: pw }).then(() => alert("Password reset."));
    else if (pw) alert("Password must be at least 8 characters.");
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    create.mutate();
  };

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Users</h1>

      <form onSubmit={onSubmit} className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
        <h3 className="mb-3 text-sm font-semibold text-gray-700">Add a user</h3>
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="email@example.com"
            required
            className={`${inputClass} w-64`}
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Initial password (min 8)"
            required
            minLength={8}
            className={`${inputClass} w-56`}
          />
          <label className="flex items-center gap-1.5 text-sm text-gray-700">
            <input type="checkbox" checked={isAdmin} onChange={(e) => setIsAdmin(e.target.checked)} />
            Admin
          </label>
          <button
            type="submit"
            disabled={create.isPending}
            className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            Create user
          </button>
        </div>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        <p className="mt-2 text-xs text-gray-400">
          Admins manage users and settings. Members can run and view scans but cannot change either.
        </p>
      </form>

      <div className="rounded-lg border border-gray-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-[11px] uppercase tracking-wider text-gray-400">
              <th className="px-4 py-2 font-semibold">Email</th>
              <th className="px-4 py-2 font-semibold">Role</th>
              <th className="px-4 py-2 font-semibold">Status</th>
              <th className="px-4 py-2 font-semibold">Created</th>
              <th className="px-4 py-2 font-semibold"></th>
            </tr>
          </thead>
          <tbody>
            {(users ?? []).map((u) => {
              const self = u.id === me?.id;
              return (
                <tr key={u.id} className="border-b border-gray-100 last:border-0">
                  <td className="px-4 py-2.5 font-medium text-gray-900">
                    {u.email}
                    {self && <span className="ml-2 text-xs text-gray-400">(you)</span>}
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                        u.is_admin ? "bg-sky-100 text-sky-700" : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {u.is_admin ? "admin" : "member"}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={u.is_active ? "text-emerald-600" : "text-gray-400"}>
                      {u.is_active ? "active" : "deactivated"}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-gray-500">
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-2.5">
                    <div className="flex flex-wrap justify-end gap-2 text-xs">
                      <button
                        onClick={() => update.mutate({ id: u.id, data: { is_admin: !u.is_admin } })}
                        disabled={self}
                        className="rounded-md border border-gray-300 px-2 py-1 font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-40"
                      >
                        {u.is_admin ? "Make member" : "Make admin"}
                      </button>
                      <button
                        onClick={() => update.mutate({ id: u.id, data: { is_active: !u.is_active } })}
                        disabled={self}
                        className="rounded-md border border-gray-300 px-2 py-1 font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-40"
                      >
                        {u.is_active ? "Deactivate" : "Activate"}
                      </button>
                      <button
                        onClick={() => resetPassword(u)}
                        className="rounded-md border border-gray-300 px-2 py-1 font-medium text-gray-600 hover:bg-gray-50"
                      >
                        Reset password
                      </button>
                      <button
                        onClick={() => {
                          if (confirm(`Delete user ${u.email}?`)) remove.mutate(u.id);
                        }}
                        disabled={self}
                        className="rounded-md border border-red-300 px-2 py-1 font-medium text-red-700 hover:bg-red-50 disabled:opacity-40"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
