"""Small QuestDB REST client used by the API read models."""

from typing import Any

import httpx


class QuestDBError(RuntimeError):
    """Raised when QuestDB cannot execute a query."""


class QuestDBClient:
    """Execute SQL through QuestDB's HTTP API and return named rows."""

    def __init__(self, address: str, timeout: float = 5.0):
        normalized = address.strip().rstrip("/")
        if not normalized.startswith(("http://", "https://")):
            normalized = f"http://{normalized}"
        self.execute_url = f"{normalized}/api/v1/sql/execute"
        self.timeout = timeout

    def query(self, sql: str) -> list[dict[str, Any]]:
        """Execute SQL and map QuestDB's column/dataset response to dictionaries."""
        try:
            response = httpx.get(self.execute_url, params={"query": sql}, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise QuestDBError(f"QuestDB query failed: {exc}") from exc

        if "error" in payload:
            raise QuestDBError(f"QuestDB query failed: {payload['error']}")

        column_names = [column["name"] for column in payload.get("columns", [])]
        return [dict(zip(column_names, values, strict=True)) for values in payload.get("dataset", [])]
