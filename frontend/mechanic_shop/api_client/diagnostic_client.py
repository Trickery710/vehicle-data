"""Concrete diagnostic session API client, backed by the shared ``ApiClient`` (httpx)."""

from __future__ import annotations

from frontend.mechanic_shop.api_client.base_client import ApiClient
from frontend.mechanic_shop.models.diagnostic import (
    DiagnosticReading,
    DiagnosticSession,
    DiagnosticTroubleCode,
)


class DiagnosticApiClient:
    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list_for_vehicle(self, vehicle_id: int) -> list[DiagnosticSession]:
        body = self._client.get(f"/vehicles/{vehicle_id}/diagnostic-sessions")
        return [DiagnosticSession.from_api(item) for item in body]

    def get_session(self, session_id: int) -> DiagnosticSession:
        return DiagnosticSession.from_api(self._client.get(f"/diagnostic-sessions/{session_id}"))

    def create_session(self, session: DiagnosticSession) -> DiagnosticSession:
        body = self._client.post("/diagnostic-sessions", json=session.to_create_payload())
        return DiagnosticSession.from_api(body)

    def update_session(self, session_id: int, session: DiagnosticSession) -> DiagnosticSession:
        body = self._client.patch(
            f"/diagnostic-sessions/{session_id}", json=session.to_update_payload()
        )
        return DiagnosticSession.from_api(body)

    def replace_trouble_codes(
        self, session_id: int, codes: list[DiagnosticTroubleCode]
    ) -> list[DiagnosticTroubleCode]:
        payload = [c.to_create_payload() for c in codes]
        body = self._client.put(f"/diagnostic-sessions/{session_id}/trouble-codes", json=payload)
        return [DiagnosticTroubleCode.from_api(c) for c in body]

    def replace_readings(
        self, session_id: int, readings: list[DiagnosticReading]
    ) -> list[DiagnosticReading]:
        payload = [r.to_create_payload() for r in readings]
        body = self._client.put(f"/diagnostic-sessions/{session_id}/readings", json=payload)
        return [DiagnosticReading.from_api(r) for r in body]
