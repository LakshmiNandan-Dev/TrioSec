import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { apiErrorMessage } from "../api/client";
import { createProject, deleteProject, listProjects } from "../api/endpoints";

export default function ProjectsPage() {
  const queryClient = useQueryClient();
  const { data: projects, isLoading } = useQuery({ queryKey: ["projects"], queryFn: listProjects });
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [gitToken, setGitToken] = useState("");
  const [error, setError] = useState("");

  const create = useMutation({
    mutationFn: () =>
      createProject({ name, description: description || null, git_token: gitToken || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setShowForm(false);
      setName("");
      setDescription("");
      setGitToken("");
      setError("");
    },
    onError: (err) => setError(apiErrorMessage(err)),
  });

  const remove = useMutation({
    mutationFn: deleteProject,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["projects"] }),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    create.mutate();
  };

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="rounded-md bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700"
        >
          {showForm ? "Cancel" : "New project"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={onSubmit} className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
          <div className="flex gap-3">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Project name"
              required
              className="w-64 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none"
            />
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Description (optional)"
              className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={create.isPending}
              className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              Create
            </button>
          </div>
          <div className="mt-3">
            <input
              type="password"
              value={gitToken}
              onChange={(e) => setGitToken(e.target.value)}
              placeholder="Git access token (optional — only needed to clone private repos)"
              autoComplete="new-password"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none"
            />
            <p className="mt-1 text-xs text-gray-400">
              A read-only Personal Access Token. Stored encrypted; used only to clone private
              repositories for this project's Git-URL scans.
            </p>
          </div>
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        </form>
      )}

      {isLoading ? (
        <p className="text-sm text-gray-400">Loading projects…</p>
      ) : projects && projects.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {projects.map((p) => (
            <div key={p.id} className="rounded-lg border border-gray-200 bg-white p-4">
              <div className="flex items-start justify-between">
                <Link
                  to={`/projects/${p.id}`}
                  className="text-base font-semibold text-sky-700 hover:underline"
                >
                  {p.name}
                </Link>
                <button
                  onClick={() => {
                    if (confirm(`Delete project "${p.name}" and all of its scans?`)) {
                      remove.mutate(p.id);
                    }
                  }}
                  className="text-xs text-gray-400 hover:text-red-600"
                >
                  delete
                </button>
              </div>
              <p className="mt-1 min-h-5 text-sm text-gray-500">{p.description || "—"}</p>
              <p className="mt-3 text-xs text-gray-400">
                Created {new Date(p.created_at).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-gray-300 p-10 text-center text-sm text-gray-400">
          No projects yet. Create one, then point a scan at your codebase or a running app.
        </div>
      )}
    </div>
  );
}
