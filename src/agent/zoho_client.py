from __future__ import annotations

import re
import time
from typing import Any

import requests

from agent.settings import Settings


class ZohoConfigError(RuntimeError):
    pass


class ZohoCreatorClient:
    """Zoho Creator v2.1 API client.

    Uses:
    - metadata endpoint to list reports
    - data endpoint to fetch report rows
    """

    def __init__(self, settings: Settings, timeout: int = 30) -> None:
        self.s = settings
        self.timeout = timeout
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    def _require_config(self) -> None:
        required = {
            "ZOHO_CLIENT_ID": self.s.zoho_client_id,
            "ZOHO_CLIENT_SECRET": self.s.zoho_client_secret,
            "ZOHO_REFRESH_TOKEN": self.s.zoho_refresh_token,
            "ZOHO_ACCOUNT_OWNER": self.s.zoho_account_owner,
            "ZOHO_APP_LINK_NAME": self.s.zoho_app_link_name,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ZohoConfigError(
                "Missing Zoho configuration: " + ", ".join(missing)
            )

    def _fetch_access_token(self) -> tuple[str, int]:
        self._require_config()
        token_url = f"{self.s.zoho_accounts_url}/oauth/v2/token"
        response = requests.post(
            token_url,
            params={
                "refresh_token": self.s.zoho_refresh_token,
                "client_id": self.s.zoho_client_id,
                "client_secret": self.s.zoho_client_secret,
                "grant_type": "refresh_token",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise ZohoConfigError("Failed to fetch Zoho OAuth access token.")
        expires_in = int(payload.get("expires_in") or payload.get("expires_in_sec") or 3600)
        return token, expires_in

    def _get_access_token(self, force_refresh: bool = False) -> str:
        now = time.time()
        if (
            not force_refresh
            and self._access_token is not None
            and now < self._token_expires_at
        ):
            return self._access_token

        token, expires_in = self._fetch_access_token()
        # Refresh slightly early to avoid edge-expiry during requests.
        refresh_buffer = min(60, max(5, expires_in // 10))
        self._access_token = token
        self._token_expires_at = now + max(1, expires_in - refresh_buffer)
        return token

    def _headers(self, force_refresh: bool = False) -> dict[str, str]:
        return {
            "Authorization": f"Zoho-oauthtoken {self._get_access_token(force_refresh=force_refresh)}",
            "Accept": "application/json",
        }

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        response = requests.request(
            method=method,
            url=url,
            headers=self._headers(force_refresh=False),
            timeout=self.timeout,
            **kwargs,
        )
        if response.status_code in {401, 403}:
            response = requests.request(
                method=method,
                url=url,
                headers=self._headers(force_refresh=True),
                timeout=self.timeout,
                **kwargs,
            )
        response.raise_for_status()
        return response

    def _creator_v21_base(self) -> str:
        return f"{self.s.zoho_base_url}/creator/v2.1"

    @staticmethod
    def _sanitize_table_name(name: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9_]+", "_", name.strip().lower())
        return safe.strip("_") or "table"

    @staticmethod
    def _extract_reports_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
        nodes: list[dict[str, Any]] = []
        candidates: list[Any] = [
            payload.get("reports"),
            payload.get("result", {}).get("reports"),
            payload.get("data", {}).get("reports"),
            payload.get("metadata", {}).get("reports"),
            payload.get("result", {}).get("metadata", {}).get("reports"),
        ]
        for c in candidates:
            if isinstance(c, list):
                nodes.extend([x for x in c if isinstance(x, dict)])

        normalized: list[dict[str, Any]] = []
        for node in nodes:
            link_name = (
                node.get("report_link_name")
                or node.get("link_name")
                or node.get("api_name")
                or node.get("name")
            )
            if not link_name:
                continue
            display_name = node.get("display_name") or node.get("name") or str(link_name)
            normalized.append(
                {
                    "name": str(display_name),
                    "report_link_name": str(link_name),
                    "table_name": ZohoCreatorClient._sanitize_table_name(str(link_name)),
                    "description": str(node.get("description") or ""),
                    "key_columns": [],
                }
            )
        return normalized

    def list_reports(self) -> list[dict[str, Any]]:
        self._require_config()
        owner = self.s.zoho_account_owner
        app = self.s.zoho_app_link_name
        base = self._creator_v21_base()
        endpoints = [
            f"{base}/meta/{owner}/{app}/reports",
        ]

        last_error: Exception | None = None
        for url in endpoints:
            try:
                response = self._request("GET", url)
                payload = response.json()
                reports = self._extract_reports_from_payload(payload)
                if reports:
                    return reports
            except Exception as exc:  # pragma: no cover - depends on external API behavior
                last_error = exc
                continue

        if last_error:
            raise RuntimeError(
                f"Unable to discover reports from Zoho metadata endpoints. Last error: {last_error}"
            )
        raise RuntimeError("Unable to discover reports from Zoho metadata endpoints.")

    @staticmethod
    def _extract_report_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
        rows = payload.get("data")
        if isinstance(rows, list):
            return [r for r in rows if isinstance(r, dict)]
        return []

    def fetch_report_rows(self, report_link_name: str) -> list[dict[str, Any]]:
        self._require_config()
        owner = self.s.zoho_account_owner
        app = self.s.zoho_app_link_name
        url = f"{self._creator_v21_base()}/data/{owner}/{app}/report/{report_link_name}"
        response = self._request("GET", url)
        payload = response.json()
        return self._extract_report_rows(payload)
