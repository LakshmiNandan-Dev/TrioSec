import os
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from app.db import SessionLocal
from app.models.app_setting import AppSetting
from app.models.project import Project
from app.models.scan import (
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_RUNNING,
    Scan,
)
from app.scanners.base import RawFinding, ScanContext
from app.scanners.iac_adapter import TrivyIacAdapter
from app.scanners.semgrep_adapter import SemgrepAdapter
from app.scanners.trivy_adapter import TrivyAdapter
from app.scanners.zap_adapter import ZapAdapter
from app.services import finding_service, path_service
from app.services.crypto import decrypt_str

ADAPTERS = {
    "sast": SemgrepAdapter,
    "sca": TrivyAdapter,
    "dast": ZapAdapter,
    "iac": TrivyIacAdapter,
}
CLONE_BASE = "/tmp/triosec"
LOG_LIMIT = 20_000

# Serializes concurrent read-modify-write updates to the scan row from tool threads.
_db_write_lock = threading.Lock()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _update_scan(scan_id: int, **fields) -> None:
    with _db_write_lock, SessionLocal() as db:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return
        for key, value in fields.items():
            setattr(scan, key, value)
        db.commit()


def _set_tool_status(scan_id: int, tool: str, value: str) -> None:
    with _db_write_lock, SessionLocal() as db:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return
        scan.tool_status = {**(scan.tool_status or {}), tool: value}
        db.commit()


def run_scan(scan_id: int) -> None:
    logs: list[str] = []

    def log(message: str) -> None:
        line = f"[{_now().strftime('%H:%M:%S')}] {message}"
        print(f"scan {scan_id}: {line}", flush=True)
        # Flush to the DB on every line so the UI can stream logs while the scan runs.
        # Tool threads call this concurrently, so guard the buffer + write together.
        with _db_write_lock:
            logs.append(line)
            snapshot = "\n".join(logs)[-LOG_LIMIT:]
            with SessionLocal() as db:
                scan = db.get(Scan, scan_id)
                if scan is not None:
                    scan.logs = snapshot
                    db.commit()

    with SessionLocal() as db:
        scan = db.get(Scan, scan_id)
        if scan is None or scan.status == STATUS_CANCELLED:
            return
        scan_types = [t for t in scan.scan_types if t in ADAPTERS]
        target_type = scan.target_type
        target_value = scan.target_value
        dast_url = scan.dast_url
        dast_full_scan = scan.dast_full_scan
        app_cfg = db.get(AppSetting, 1)
        semgrep_config = (app_cfg.default_semgrep_config if app_cfg else None) or "p/default"
        project = db.get(Project, scan.project_id)
        git_token_enc = project.git_token_encrypted if project else None

    _update_scan(scan_id, status=STATUS_RUNNING, started_at=_now())

    clone_dir: str | None = None
    results: list[RawFinding] = []
    failures: dict[str, str] = {}
    try:
        scan_root = None
        if any(t in scan_types for t in ("sast", "sca", "iac")):
            if target_type == "git_url":
                clone_dir = os.path.join(CLONE_BASE, str(scan_id))
                shutil.rmtree(clone_dir, ignore_errors=True)
                os.makedirs(CLONE_BASE, exist_ok=True)
                token = None
                if git_token_enc:
                    try:
                        token = decrypt_str(git_token_enc)
                    except ValueError as exc:
                        log(f"warning: could not decrypt git token ({exc}); trying anonymous clone")
                log(f"cloning {target_value}" + (" (with access token)" if token else ""))
                path_service.clone_git_url(target_value, clone_dir, token=token)
                scan_root = clone_dir
            else:
                scan_root = path_service.resolve_workspace_path(target_value or "")

        ctx = ScanContext(
            scan_root=scan_root,
            dast_url=dast_url,
            dast_full_scan=dast_full_scan,
            semgrep_config=semgrep_config,
            log=log,
        )

        def run_tool(tool: str) -> list[RawFinding]:
            _set_tool_status(scan_id, tool, STATUS_RUNNING)
            try:
                found = ADAPTERS[tool]().run(ctx)
            except Exception as exc:  # noqa: BLE001 — one tool failing must not sink the scan
                failures[tool] = str(exc)
                log(f"{tool} FAILED: {exc}")
                _set_tool_status(scan_id, tool, STATUS_FAILED)
                return []
            _set_tool_status(scan_id, tool, STATUS_COMPLETED)
            return found

        with ThreadPoolExecutor(max_workers=len(scan_types)) as pool:
            for tool_findings in pool.map(run_tool, scan_types):
                results.extend(tool_findings)

        with SessionLocal() as db:
            scan = db.get(Scan, scan_id)
            if scan is None or scan.status == STATUS_CANCELLED:
                return
            counts, total = finding_service.persist_findings(db, scan, results)
            scan.severity_counts = counts
            scan.total_findings = total
            scan.status = STATUS_FAILED if len(failures) == len(scan_types) else STATUS_COMPLETED
            if failures:
                scan.error_message = "; ".join(f"{t}: {m[:300]}" for t, m in failures.items())
            scan.finished_at = _now()
            scan.logs = "\n".join(logs)[-LOG_LIMIT:]
            db.commit()
        log(f"scan finished: {len(results)} raw findings")
    except Exception as exc:  # noqa: BLE001
        log(f"scan failed: {exc}")
        _update_scan(
            scan_id,
            status=STATUS_FAILED,
            error_message=str(exc)[:2000],
            finished_at=_now(),
            logs="\n".join(logs)[-LOG_LIMIT:],
        )
        raise
    finally:
        if clone_dir:
            shutil.rmtree(clone_dir, ignore_errors=True)
