"""HTTP client wrapper for the local FastAPI backend.

Maps HTTP status codes to typed exceptions so ViewModels can distinguish
"fix this field" (validation) from "this doesn't exist" (not found) from
"the backend isn't reachable" (connection) without inspecting status codes
themselves.
"""

from __future__ import annotations

from typing import Any

import httpx


class ApiError(Exception):
    """Base class for all API client errors."""


class ApiConnectionError(ApiError):
    """The backend could not be reached at all (network/process down)."""


class ApiNotFoundError(ApiError):
    """404 -- the requested entity does not exist."""


class ApiValidationError(ApiError):
    """422 -- request failed validation. ``detail`` carries FastAPI's error body."""

    def __init__(self, message: str, detail: Any = None) -> None:
        super().__init__(message)
        self.detail = detail


class ApiConflictError(ApiError):
    """409 -- request conflicts with current server state."""


class ApiServerError(ApiError):
    """5xx -- unexpected backend failure."""


class ApiClient:
    def __init__(self, base_url: str, timeout_seconds: float = 10.0) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout_seconds)

    def close(self) -> None:
        self._client.close()

    def get(self, path: str, params: dict | None = None) -> Any:
        return self._request("GET", path, params=params)

    def post(self, path: str, json: dict | None = None) -> Any:
        return self._request("POST", path, json=json)

    def patch(self, path: str, json: dict | None = None) -> Any:
        return self._request("PATCH", path, json=json)

    def put(self, path: str, json: dict | list | None = None) -> Any:
        return self._request("PUT", path, json=json)

    def delete(self, path: str) -> Any:
        return self._request("DELETE", path)

    def post_multipart(self, path: str, data: dict, files: dict) -> Any:
        """``data`` becomes multipart form fields, ``files`` is httpx's
        ``files=`` mapping (e.g. ``{"file": (filename, bytes, content_type)}``)."""
        return self._request("POST", path, data=data, files=files)

    def get_bytes(self, path: str) -> tuple[bytes, str]:
        """Returns ``(content, content_type)`` for binary responses
        (attachment downloads, PDF export) that aren't JSON."""
        try:
            response = self._client.request("GET", path)
        except httpx.RequestError as exc:
            raise ApiConnectionError(
                f"Could not reach the backend at {self._client.base_url}{path}: {exc}"
            ) from exc

        if response.status_code == 404:
            raise ApiNotFoundError(_error_detail(response))
        if response.status_code >= 500:
            raise ApiServerError(_error_detail(response))
        response.raise_for_status()
        return response.content, response.headers.get("content-type", "application/octet-stream")

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.RequestError as exc:
            raise ApiConnectionError(
                f"Could not reach the backend at {self._client.base_url}{path}: {exc}"
            ) from exc

        if response.status_code == 404:
            raise ApiNotFoundError(_error_detail(response))
        if response.status_code == 409:
            raise ApiConflictError(_error_detail(response))
        if response.status_code == 422:
            body = _safe_json(response)
            raise ApiValidationError(
                _error_detail(response), detail=body.get("detail") if body else None
            )
        if response.status_code >= 500:
            raise ApiServerError(_error_detail(response))
        response.raise_for_status()

        if response.status_code == 204 or not response.content:
            return None
        return response.json()


def _safe_json(response: httpx.Response) -> dict | None:
    try:
        return response.json()
    except ValueError:
        return None


def _error_detail(response: httpx.Response) -> str:
    body = _safe_json(response)
    if body and isinstance(body, dict) and "detail" in body:
        return str(body["detail"])
    return f"HTTP {response.status_code}: {response.text}"
