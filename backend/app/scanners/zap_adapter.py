import time
from collections.abc import Callable

import httpx

from app.config import settings
from app.scanners import severity
from app.scanners.base import RawFinding, ScanContext, ScannerAdapter


class ZapError(RuntimeError):
    pass


class ZapAdapter(ScannerAdapter):
    name = "zap"

    PASSIVE_TIMEOUT = 5 * 60
    ACTIVE_TIMEOUT = 90 * 60
    POLL_INTERVAL = 5

    def run(self, ctx: ScanContext) -> list[RawFinding]:
        with httpx.Client(
            base_url=settings.zap_base_url,
            params={"apikey": settings.zap_api_key},
            timeout=60,
        ) as client:
            return self._run(client, ctx)

    def _get(self, client: httpx.Client, path: str, **params) -> dict:
        response = client.get(path, params=params)
        if response.status_code >= 400:
            raise ZapError(f"ZAP API error {response.status_code}: {response.text[:300]}")
        return response.json()

    def _wait_until(
        self,
        condition: Callable[[], bool],
        timeout: int,
        stage: str,
        ctx: ScanContext,
        describe: Callable[[], str] | None = None,
    ) -> bool:
        """Poll until `condition` is true. Returns True if it completed, False on timeout.

        Never raises on timeout — the caller decides how to proceed so a long-running
        stage degrades gracefully instead of failing the whole scan. `describe` yields
        a live progress line (e.g. crawl %) so the UI shows real movement, not a spinner.
        """
        deadline = time.monotonic() + timeout
        last_log = 0.0
        while True:
            try:
                if condition():
                    return True
            except ZapError as exc:
                ctx.log(f"zap: {stage} status check failed, retrying: {exc}")
            if time.monotonic() > deadline:
                return False
            if time.monotonic() - last_log > 20:
                try:
                    msg = describe() if describe else f"{stage} in progress…"
                except ZapError:
                    msg = f"{stage} in progress…"
                ctx.log(f"zap: {msg}")
                last_log = time.monotonic()
            time.sleep(self.POLL_INTERVAL)

    def _run(self, client: httpx.Client, ctx: ScanContext) -> list[RawFinding]:
        url = ctx.dast_url
        if not url:
            raise ZapError("No DAST target URL provided")

        # Fresh session so alerts from earlier scans don't bleed into this one.
        self._get(client, "/JSON/core/action/newSession/", name=f"triosec-{int(time.time())}", overwrite="true")

        # Bound the crawl so a large or JS-heavy site can't run forever. ZAP enforces
        # maxDuration internally, so the spider reaches 100% on its own within the cap.
        max_minutes = max(1, settings.zap_spider_max_duration_min)
        self._get(client, "/JSON/spider/action/setOptionMaxDuration/", Integer=max_minutes)
        self._get(client, "/JSON/spider/action/setOptionMaxDepth/", Integer=settings.zap_spider_max_depth)
        spider_timeout = max_minutes * 60 + 120  # safety net above ZAP's own limit

        ctx.log(f"zap: spidering {url} (max {max_minutes} min)")
        spider_id = self._get(client, "/JSON/spider/action/scan/", url=url)["scan"]

        def spider_progress() -> str:
            pct = self._get(client, "/JSON/spider/view/status/", scanId=spider_id)["status"]
            found = self._get(client, "/JSON/spider/view/results/", scanId=spider_id).get("results", [])
            return f"spider {pct}% — {len(found)} URLs found"

        if not self._wait_until(
            lambda: int(self._get(client, "/JSON/spider/view/status/", scanId=spider_id)["status"]) >= 100,
            spider_timeout, "spider", ctx, describe=spider_progress,
        ):
            ctx.log("zap: spider hit the time limit — stopping it and continuing with what was crawled")
            try:
                self._get(client, "/JSON/spider/action/stop/", scanId=spider_id)
            except ZapError:
                pass

        ctx.log("zap: waiting for passive scan to finish")
        if not self._wait_until(
            lambda: int(self._get(client, "/JSON/pscan/view/recordsToScan/")["recordsToScan"]) == 0,
            self.PASSIVE_TIMEOUT, "passive scan", ctx,
            describe=lambda: "passive scan — "
            f"{self._get(client, '/JSON/pscan/view/recordsToScan/')['recordsToScan']} records left",
        ):
            ctx.log("zap: passive scan still draining — continuing with current results")

        if ctx.dast_full_scan:
            ctx.log("zap: starting full active scan (this can take a long time)")
            ascan_id = self._get(client, "/JSON/ascan/action/scan/", url=url)["scan"]
            if not self._wait_until(
                lambda: int(self._get(client, "/JSON/ascan/view/status/", scanId=ascan_id)["status"]) >= 100,
                self.ACTIVE_TIMEOUT, "active scan", ctx,
                describe=lambda: "active scan "
                f"{self._get(client, '/JSON/ascan/view/status/', scanId=ascan_id)['status']}%",
            ):
                ctx.log("zap: active scan hit the time limit — stopping it and continuing")
                try:
                    self._get(client, "/JSON/ascan/action/stop/", scanId=ascan_id)
                except ZapError:
                    pass

        alerts = self._get(client, "/JSON/core/view/alerts/", baseurl=url, start=0, count=9999)["alerts"]
        findings = []
        for alert in alerts:
            cwe_id = str(alert.get("cweid") or "").strip()
            cwe = f"CWE-{cwe_id}" if cwe_id and cwe_id not in ("-1", "0") else None
            findings.append(
                RawFinding(
                    tool="zap",
                    category="dast",
                    severity=severity.from_zap(alert.get("risk")),
                    title=alert.get("alert") or alert.get("name") or "ZAP alert",
                    description=alert.get("description"),
                    rule_id=str(alert.get("pluginId") or "") or None,
                    cwe=cwe,
                    url=alert.get("url"),
                    remediation=alert.get("solution"),
                    raw=alert,
                )
            )
        ctx.log(f"zap: {len(findings)} raw alerts")
        return findings
