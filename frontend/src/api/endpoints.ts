import { api } from "./client";
import type {
  AppSettings,
  AuditFilters,
  AuditPage,
  CompareResult,
  Finding,
  FindingFilters,
  FindingPage,
  HealthStatus,
  Project,
  Scan,
  ScanCreate,
  TrendPoint,
  User,
} from "./types";

// auth
export const login = (email: string, password: string) =>
  api.post<{ access_token: string }>("/auth/login", { email, password }).then((r) => r.data);
export const getMe = () => api.get<User>("/auth/me").then((r) => r.data);
export const changePassword = (current_password: string, new_password: string) =>
  api.post("/auth/change-password", { current_password, new_password }).then((r) => r.data);

// users (admin)
export const listUsers = () => api.get<User[]>("/users").then((r) => r.data);
export const createUser = (email: string, password: string, is_admin: boolean) =>
  api.post<User>("/users", { email, password, is_admin }).then((r) => r.data);
export const updateUser = (
  id: number,
  data: { is_admin?: boolean; is_active?: boolean; password?: string },
) => api.patch<User>(`/users/${id}`, data).then((r) => r.data);
export const deleteUser = (id: number) => api.delete(`/users/${id}`);

// health
export const getHealth = () => api.get<HealthStatus>("/health").then((r) => r.data);

// projects
export const listProjects = () => api.get<Project[]>("/projects").then((r) => r.data);
export const getProject = (id: number) => api.get<Project>(`/projects/${id}`).then((r) => r.data);
export const createProject = (data: {
  name: string;
  description?: string | null;
  git_token?: string;
}) => api.post<Project>("/projects", data).then((r) => r.data);
export const updateProject = (
  id: number,
  data: { git_token?: string; clear_git_token?: boolean },
) => api.put<Project>(`/projects/${id}`, data).then((r) => r.data);
export const deleteProject = (id: number) => api.delete(`/projects/${id}`);
export const getTrends = (projectId: number) =>
  api.get<TrendPoint[]>(`/projects/${projectId}/trends`).then((r) => r.data);
export const compareScans = (projectId: number, base: number, head: number) =>
  api
    .get<CompareResult>(`/projects/${projectId}/compare`, { params: { base, head } })
    .then((r) => r.data);

// scans
export const createScan = (data: ScanCreate) => api.post<Scan>("/scans", data).then((r) => r.data);
export const listScans = (projectId?: number) =>
  api.get<Scan[]>("/scans", { params: { project_id: projectId } }).then((r) => r.data);
export const getScan = (id: number) => api.get<Scan>(`/scans/${id}`).then((r) => r.data);
export const getScanLogs = (id: number) =>
  api.get<{ logs: string }>(`/scans/${id}/logs`).then((r) => r.data.logs);
export const cancelScan = (id: number) => api.post<Scan>(`/scans/${id}/cancel`).then((r) => r.data);

// findings
export const listFindings = (scanId: number, filters: FindingFilters) =>
  api
    .get<FindingPage>("/findings", { params: { scan_id: scanId, ...filters } })
    .then((r) => r.data);
export const getFinding = (id: number) => api.get<Finding>(`/findings/${id}`).then((r) => r.data);

// reports
export async function downloadReport(scanId: number, format: "json" | "html" | "pdf") {
  const response = await api.get(`/reports/scan/${scanId}.${format}`, { responseType: "blob" });
  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = `triosec-scan-${scanId}.${format}`;
  link.click();
  URL.revokeObjectURL(url);
}
export const emailReport = (scanId: number, recipient: string) =>
  api.post(`/reports/scan/${scanId}/email`, { recipient }).then((r) => r.data);

// settings
export const getSettings = () => api.get<AppSettings>("/settings").then((r) => r.data);
export const updateSettings = (data: Partial<AppSettings> & { smtp_password?: string }) =>
  api.put<AppSettings>("/settings", data).then((r) => r.data);
export const testSmtp = (recipient: string) =>
  api.post("/settings/smtp/test", { recipient }).then((r) => r.data);

// audit (admin)
export const listAudit = (filters: AuditFilters) =>
  api.get<AuditPage>("/audit", { params: filters }).then((r) => r.data);
