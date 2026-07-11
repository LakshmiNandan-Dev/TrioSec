# TrioSec

Self-hostable application-security platform that wraps three open source scanners behind one web UI:

| Capability | Tool | What it finds |
|---|---|---|
| **SAST** | [Semgrep](https://semgrep.dev) | insecure code patterns (injection, XSS, crypto misuse, …) |
| **SCA** | [Trivy](https://trivy.dev) | known CVEs in dependencies + hardcoded secrets |
| **DAST** | [OWASP ZAP](https://www.zaproxy.org) | runtime vulnerabilities in a running web app |

Deploy it with Docker Compose, then use the web interface to point scans at your local
codebases (a mounted folder or a Git URL) and running apps (any URL). Results are normalized
into a single findings model with severity filtering, run-over-run trends, exportable
JSON/HTML/PDF reports, and email delivery.

## Quick start

```bash
cp .env.example .env
# edit .env:
#   WORKSPACE_ROOT  -> absolute path to the folder that contains code you want to scan
#   JWT_SECRET, SECRET_ENCRYPTION_KEY, ZAP_API_KEY -> openssl rand -hex 32
#   ADMIN_EMAIL / ADMIN_PASSWORD -> your initial login

docker compose up -d --build
```

Open **http://localhost:8080** and sign in with the admin credentials from `.env`.

First boot notes:
- The worker pre-downloads Trivy's vulnerability DB (a few hundred MB) — the first SCA scan
  may wait on this.
- ZAP takes ~30–60s to come up; the sidebar health dots show when everything is ready.

## Using it

1. **Create a project** (e.g. "payments-api").
2. **New scan** — pick the analyses to run:
   - **SAST / SCA** need a code target: a path relative to `WORKSPACE_ROOT`
     (e.g. `my-app`) or an `https://…` Git URL that gets shallow-cloned.
   - **DAST** needs the URL of a *running* app. For an app on the host machine use
     `http://host.docker.internal:<port>` — `localhost` inside a container is the container.
     DAST defaults to a passive baseline scan; tick *full active scan* for deeper (and
     intrusive) testing, only against apps you own.
3. **Watch progress** — per-tool status updates live; findings appear when the scan finishes.
4. **Explore findings** — filter by severity / tool / category, mark-as-new highlighting,
   click a row for full detail incl. raw tool output.
5. **Trends & compare** — the project page charts severity counts across runs and can diff
   two runs (added / fixed / unchanged, by stable finding fingerprints).
6. **Reports** — download JSON / HTML / PDF, or email the PDF (configure SMTP under
   *Settings* first; the SMTP password is stored encrypted).

### Testing email locally

```bash
cp docker-compose.override.yml.example docker-compose.override.yml
docker compose up -d mailpit
```

Settings → host `mailpit`, port `1025`, TLS off. Mail arrives at http://localhost:8025.

### Single sign-on with Microsoft Entra ID (optional)

1. In the [Entra admin center](https://entra.microsoft.com): **App registrations → New
   registration** — single tenant, redirect URI (type **Web**):
   `http://localhost:8080/api/auth/sso/callback` (match your host/port).
2. Create a client secret under **Certificates & secrets**.
3. Fill in `.env`: `ENTRA_TENANT_ID`, `ENTRA_CLIENT_ID`, `ENTRA_CLIENT_SECRET`,
   `SSO_REDIRECT_URI` — all four set enables the *Sign in with Microsoft* button;
   restart with `docker compose up -d backend`.

Notes:
- Users are auto-provisioned on first SSO login (as non-admin) and cannot use
  password login; the seeded admin keeps working as a break-glass account.
- Optional role mapping: define an app role named `TrioSec.Admin` on the registration
  and assign it to users — it syncs to TrioSec's admin flag on every SSO login
  (never demoting the last active admin). Without app roles, manage roles in TrioSec.
- For `npm run dev`, register `http://localhost:5173/api/auth/sso/callback` as an
  extra redirect URI and point `SSO_REDIRECT_URI` at it (vite proxies `/api`).

### Try it against something deliberately vulnerable

```bash
# DAST target
docker run -d -p 3000:3000 bkimminich/juice-shop
# scan http://host.docker.internal:3000

# SAST/SCA target — clone a vulnerable app into your workspace
git clone https://github.com/OWASP/NodeGoat "$WORKSPACE_ROOT/nodegoat"
# scan local path: nodegoat
```

## Architecture

```
frontend (React+nginx :8080) ─→ backend (FastAPI) ─→ Postgres
                                     │  enqueue           ▲
                                     ▼                    │ findings
                                   Redis ──→ worker (RQ) ─┘
                                              │ subprocess: semgrep, trivy, git
                                              └ REST: ZAP daemon ──→ your running app
                          /workspace (read-only mount of WORKSPACE_ROOT)
```

- Findings from all tools are normalized into one model with a canonical severity scale
  and a stable SHA-256 fingerprint per finding (rule+location for SAST, CVE+package for SCA,
  plugin+URL+param for DAST) — used for dedup, "new" detection, and run comparison.
- Scan paths are validated to stay inside the read-only `/workspace` mount; scanners are
  invoked with argument lists (never a shell).
- The API refuses to boot with placeholder `JWT_SECRET` / `SECRET_ENCRYPTION_KEY`.

## Development

```bash
# backend (needs Postgres+Redis, e.g. docker compose up -d db redis zap)
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload           # http://localhost:8000/docs

# frontend (proxies /api to :8000)
cd frontend && npm install && npm run dev   # http://localhost:5173
```

`make up / down / logs / migrate` wrap the common compose commands.
