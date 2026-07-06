export const SEVERITIES = ["critical", "high", "medium", "low", "info"] as const;
export type Severity = (typeof SEVERITIES)[number];

export const SEVERITY_COLORS: Record<Severity, string> = {
  critical: "#d03b3b",
  high: "#ec835a",
  medium: "#c98500",
  low: "#2a78d6",
  info: "#4a3aa7",
};

export interface User {
  id: number;
  email: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
}

export interface Project {
  id: number;
  name: string;
  description: string | null;
  default_target_type: string | null;
  default_target_value: string | null;
  has_git_token: boolean;
  created_at: string;
}

export interface Scan {
  id: number;
  project_id: number;
  status: string;
  scan_types: string[];
  target_type: string | null;
  target_value: string | null;
  dast_url: string | null;
  dast_full_scan: boolean;
  authorized_by: string | null;
  tool_status: Record<string, string>;
  severity_counts: Record<string, number> | null;
  total_findings: number;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface ScanCreate {
  project_id: number;
  scan_types: string[];
  target_type?: string | null;
  target_value?: string | null;
  dast_url?: string | null;
  dast_full_scan?: boolean;
  authorization_acknowledged?: boolean;
}

export interface Finding {
  id: number;
  scan_id: number;
  tool: string;
  category: string;
  severity: Severity;
  title: string;
  description: string | null;
  rule_id: string | null;
  cwe: string | null;
  cve: string | null;
  file_path: string | null;
  line_start: number | null;
  line_end: number | null;
  url: string | null;
  package_name: string | null;
  installed_version: string | null;
  fixed_version: string | null;
  fingerprint: string;
  is_new: boolean;
  remediation: string | null;
  raw: Record<string, unknown> | null;
}

export interface FindingBrief {
  id: number;
  tool: string;
  category: string;
  severity: Severity;
  title: string;
  file_path: string | null;
  url: string | null;
  package_name: string | null;
}

export interface FindingPage {
  items: Finding[];
  total: number;
  page: number;
  page_size: number;
}

export interface FindingFilters {
  severity?: string;
  tool?: string;
  category?: string;
  is_new?: boolean;
  q?: string;
  page?: number;
  page_size?: number;
}

export interface TrendPoint {
  scan_id: number;
  finished_at: string | null;
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
  total: number;
}

export interface CompareResult {
  base_scan_id: number;
  head_scan_id: number;
  added: FindingBrief[];
  fixed: FindingBrief[];
  unchanged_count: number;
}

export interface AppSettings {
  smtp_host: string | null;
  smtp_port: number;
  smtp_username: string | null;
  smtp_use_tls: boolean;
  smtp_from_address: string | null;
  default_semgrep_config: string;
  dast_allowed_domains: string | null;
  has_smtp_password: boolean;
}

export interface HealthStatus {
  db: boolean;
  redis: boolean;
  zap: boolean;
  ok: boolean;
}

export interface AuditEvent {
  id: number;
  created_at: string;
  action: string;
  actor_email: string | null;
  target: string | null;
  ip: string | null;
  detail: Record<string, unknown> | null;
}

export interface AuditPage {
  items: AuditEvent[];
  total: number;
  page: number;
  page_size: number;
}

export interface AuditFilters {
  action?: string;
  actor?: string;
  q?: string;
  page?: number;
  page_size?: number;
}
