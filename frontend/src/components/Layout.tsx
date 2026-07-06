import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { getHealth } from "../api/endpoints";
import { useAuth } from "../auth/AuthContext";
import { useMe } from "../auth/useMe";
import ChangePasswordModal from "./ChangePasswordModal";

function HealthDot({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span className="flex items-center gap-1.5 text-xs text-gray-400">
      <span className={`h-2 w-2 rounded-full ${ok ? "bg-emerald-500" : "bg-red-500"}`} />
      {label}
    </span>
  );
}

export default function Layout() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const { data: me } = useMe();
  const [showChangePw, setShowChangePw] = useState(false);
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30_000,
  });

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `block rounded-md px-3 py-2 text-sm font-medium ${
      isActive ? "bg-slate-700 text-white" : "text-slate-300 hover:bg-slate-800 hover:text-white"
    }`;

  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="flex w-56 flex-col bg-slate-900 p-4">
        <div className="mb-8 px-3">
          <span className="text-lg font-bold text-white">
            Trio<span className="text-sky-400">Sec</span>
          </span>
          <p className="text-[11px] text-slate-400">SAST · SCA · DAST · IaC</p>
        </div>
        <nav className="space-y-1">
          <NavLink to="/" end className={linkClass}>
            Projects
          </NavLink>
          {me?.is_admin && (
            <>
              <NavLink to="/users" className={linkClass}>
                Users
              </NavLink>
              <NavLink to="/audit" className={linkClass}>
                Audit log
              </NavLink>
              <NavLink to="/settings" className={linkClass}>
                Settings
              </NavLink>
            </>
          )}
        </nav>
        <div className="mt-auto space-y-3">
          <div className="space-y-1 border-t border-slate-800 pt-3">
            <HealthDot ok={!!health?.db} label="Database" />
            <HealthDot ok={!!health?.redis} label="Queue" />
            <HealthDot ok={!!health?.zap} label="ZAP engine" />
          </div>
          <div className="border-t border-slate-800 pt-3">
            {me && (
              <div className="px-3 pb-1">
                <p className="truncate text-xs font-medium text-slate-200">{me.email}</p>
                <p className="text-[11px] text-slate-500">{me.is_admin ? "admin" : "member"}</p>
              </div>
            )}
            <button
              onClick={() => setShowChangePw(true)}
              className="w-full rounded-md px-3 py-2 text-left text-sm text-slate-400 hover:bg-slate-800 hover:text-white"
            >
              Change password
            </button>
            <button
              onClick={() => {
                logout();
                navigate("/login");
              }}
              className="w-full rounded-md px-3 py-2 text-left text-sm text-slate-400 hover:bg-slate-800 hover:text-white"
            >
              Sign out
            </button>
          </div>
        </div>
      </aside>
      <main className="flex-1 overflow-x-hidden p-8">
        <Outlet />
      </main>
      {showChangePw && <ChangePasswordModal onClose={() => setShowChangePw(false)} />}
    </div>
  );
}
