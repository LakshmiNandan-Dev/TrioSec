import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

/** Landing page for the SSO redirect: reads the token (or error) from the URL
 *  fragment, which never reaches any server log. */
export default function AuthCallbackPage() {
  const { loginWithToken } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.hash.slice(1));
    const token = params.get("token");
    if (token) {
      loginWithToken(token);
      navigate("/", { replace: true });
    } else {
      setError(params.get("error") || "Sign-in failed: no token received.");
    }
    // Run once on mount; the fragment does not change afterwards.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-900">
      <div className="w-full max-w-sm rounded-xl bg-white p-8 text-center shadow-xl">
        {error ? (
          <>
            <p className="mb-4 text-sm text-red-600">{error}</p>
            <Link to="/login" className="text-sm font-semibold text-sky-600 hover:underline">
              Back to sign in
            </Link>
          </>
        ) : (
          <p className="text-sm text-gray-500">Signing you in…</p>
        )}
      </div>
    </div>
  );
}
