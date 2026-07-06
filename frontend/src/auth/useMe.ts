import { useQuery } from "@tanstack/react-query";
import { getMe } from "../api/endpoints";
import { useAuth } from "./AuthContext";

/** Current logged-in user (role, email). Only fetched when authenticated. */
export function useMe() {
  const { token } = useAuth();
  return useQuery({ queryKey: ["me"], queryFn: getMe, enabled: !!token });
}
