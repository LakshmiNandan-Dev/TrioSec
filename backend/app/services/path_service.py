import os
import re
import subprocess
from urllib.parse import urlsplit

from app.config import settings


class TargetValidationError(ValueError):
    pass


def resolve_workspace_path(user_path: str) -> str:
    """Map a user-supplied path onto the mounted workspace and refuse anything outside it.

    Accepts a path relative to WORKSPACE_ROOT, the absolute host path (if it starts
    with WORKSPACE_ROOT), or the container path (/workspace/...).
    """
    root = os.path.realpath(settings.workspace_container_root)
    p = (user_path or "").strip()
    if not p:
        raise TargetValidationError("A code path is required for SAST/SCA scans")

    for prefix in (settings.workspace_root.rstrip("/"), settings.workspace_container_root.rstrip("/")):
        if prefix and (p == prefix or p.startswith(prefix + "/")):
            p = os.path.relpath(p, prefix)
            break
    if os.path.isabs(p):
        raise TargetValidationError(
            "Path must be inside WORKSPACE_ROOT — use a path relative to it or the full host path under it"
        )

    resolved = os.path.realpath(os.path.join(root, p))
    if resolved != root and os.path.commonpath([resolved, root]) != root:
        raise TargetValidationError("Path escapes the workspace")
    if not os.path.isdir(resolved):
        raise TargetValidationError(f"No such directory under the workspace: {p}")
    return resolved


def validate_git_url(url: str) -> str:
    u = (url or "").strip()
    if not u.startswith(("http://", "https://")) or " " in u:
        raise TargetValidationError("Git URL must be an http(s) URL")
    return u


def validate_dast_url(url: str) -> str:
    u = (url or "").strip()
    if not u.startswith(("http://", "https://")):
        raise TargetValidationError("DAST target must be an http(s) URL")
    return u


def parse_domain_list(raw: str | None) -> list[str]:
    """Split an admin-entered allowlist (commas/newlines/spaces) into normalized hosts."""
    if not raw:
        return []
    parts = re.split(r"[\s,]+", raw.strip())
    return [p.strip().lower().lstrip("*.") for p in parts if p.strip()]


def dast_host_allowed(url: str, allowed: list[str]) -> bool:
    """True if the URL's host equals or is a subdomain of an allowed domain."""
    host = (urlsplit(url).hostname or "").lower()
    if not host:
        return False
    return any(host == d or host.endswith("." + d) for d in allowed)


def clone_git_url(url: str, dest: str, token: str | None = None) -> None:
    # For private repos over https, inject the token as basic-auth userinfo.
    # (x-access-token works for GitHub PATs/App tokens; also accepted by GitLab/Azure DevOps.)
    clone_url = url
    if token and url.startswith("https://"):
        clone_url = url.replace("https://", f"https://x-access-token:{token}@", 1)

    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    result = subprocess.run(
        ["git", "clone", "--depth", "1", clone_url, dest],
        capture_output=True,
        text=True,
        timeout=600,
        env=env,
    )
    if result.returncode != 0:
        err = result.stderr.strip()[-500:]
        if token:  # never surface the token in an error message / logs
            err = err.replace(token, "***")
        raise RuntimeError(f"git clone failed: {err}")
