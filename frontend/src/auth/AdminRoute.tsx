import { Navigate, Outlet } from "react-router-dom";
import { useMe } from "./useMe";

/** Gate a route to admins. Members are redirected to the home page. */
export default function AdminRoute() {
  const { data: me, isLoading } = useMe();
  if (isLoading) return <p className="p-8 text-sm text-gray-400">Loading…</p>;
  if (!me?.is_admin) return <Navigate to="/" replace />;
  return <Outlet />;
}
