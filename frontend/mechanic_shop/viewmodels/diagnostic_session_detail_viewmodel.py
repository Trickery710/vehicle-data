"""Diagnostic session detail ViewModel: create/edit a diagnostic session,
its trouble codes, and its readings. ``session_id=None`` means "create
mode" -- mirrors ``EstimateDetailViewModel``'s "create unlocks in place"
pattern (the trouble-code/reading editors only unlock after the first save).
"""

from __future__ import annotations

from PySide6.QtCore import Signal

from frontend.mechanic_shop.api_client.protocols import DiagnosticApiClientProtocol
from frontend.mechanic_shop.models.diagnostic import (
    DiagnosticReading,
    DiagnosticSession,
    DiagnosticTroubleCode,
)
from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel


class DiagnosticSessionDetailViewModel(BaseViewModel):
    session_loaded = Signal()
    saved = Signal(int)

    def __init__(
        self,
        diagnostic_client: DiagnosticApiClientProtocol,
        vehicle_id: int,
        session_id: int | None = None,
    ) -> None:
        super().__init__()
        self._client = diagnostic_client
        self.vehicle_id = vehicle_id
        self.session_id = session_id
        self.session = DiagnosticSession(id=None, vehicle_id=vehicle_id)

    @property
    def is_new(self) -> bool:
        return self.session_id is None

    def load(self) -> None:
        if self.session_id is None:
            self.session_loaded.emit()
            return

        def _fetch() -> DiagnosticSession:
            return self._client.get_session(self.session_id)  # type: ignore[arg-type]

        def _on_success(session: DiagnosticSession) -> None:
            self.session = session
            self.session_loaded.emit()

        self.run_in_background(_fetch, on_success=_on_success)

    def save(self) -> None:
        def _do() -> DiagnosticSession:
            if self.is_new:
                return self._client.create_session(self.session)
            return self._client.update_session(self.session_id, self.session)  # type: ignore[arg-type]

        def _on_success(session: DiagnosticSession) -> None:
            self.session = session
            self.session_id = session.id
            self.saved.emit(session.id)

        self.run_in_background(_do, on_success=_on_success)

    def replace_trouble_codes(self, codes: list[DiagnosticTroubleCode]) -> None:
        if self.session_id is None:
            return

        def _do() -> list[DiagnosticTroubleCode]:
            return self._client.replace_trouble_codes(self.session_id, codes)  # type: ignore[arg-type]

        def _on_success(updated: list[DiagnosticTroubleCode]) -> None:
            self.session.trouble_codes = updated
            self.session_loaded.emit()

        self.run_in_background(_do, on_success=_on_success)

    def replace_readings(self, readings: list[DiagnosticReading]) -> None:
        if self.session_id is None:
            return

        def _do() -> list[DiagnosticReading]:
            return self._client.replace_readings(self.session_id, readings)  # type: ignore[arg-type]

        def _on_success(updated: list[DiagnosticReading]) -> None:
            self.session.readings = updated
            self.session_loaded.emit()

        self.run_in_background(_do, on_success=_on_success)
