import { useQueryClient } from "@tanstack/react-query";
import { createContext, useContext, useState, type ReactNode } from "react";
import { TOKEN_KEY } from "../api/client";
import { login as apiLogin } from "../api/endpoints";

interface AuthValue {
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  /** Store a token obtained outside the password flow (e.g. the SSO callback). */
  loginWithToken: (accessToken: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const queryClient = useQueryClient();

  const loginWithToken = (accessToken: string) => {
    // Drop any cached data from a previous session (e.g. another user on this browser).
    queryClient.clear();
    localStorage.setItem(TOKEN_KEY, accessToken);
    setToken(accessToken);
  };

  const login = async (email: string, password: string) => {
    const { access_token } = await apiLogin(email, password);
    loginWithToken(access_token);
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    queryClient.clear();
  };

  return (
    <AuthContext.Provider value={{ token, login, loginWithToken, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
