"""Base ViewModel with a background-thread helper for API calls.

``httpx`` calls block. Calling the API client directly from a button-click
slot would freeze the whole UI, so every ViewModel method that talks to the
backend goes through ``run_in_background``, which runs the call on
``QThreadPool`` and marshals the result back to the GUI thread via Qt
signals (safe across threads under the default ``Qt.AutoConnection``).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from frontend.mechanic_shop.api_client.base_client import (
    ApiConflictError,
    ApiConnectionError,
    ApiNotFoundError,
    ApiServerError,
    ApiValidationError,
)


class _WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(object)


class _Worker(QRunnable):
    def __init__(self, fn: Callable[[], Any]) -> None:
        super().__init__()
        self._fn = fn
        self.signals = _WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self._fn()
        except Exception as exc:  # noqa: BLE001 -- forwarded to the GUI thread, not swallowed
            self.signals.error.emit(exc)
        else:
            self.signals.finished.emit(result)


def format_api_error(exc: Exception) -> str:
    """Turns a caught exception into a user-facing message for status bars/dialogs."""
    if isinstance(exc, ApiConnectionError):
        return "Could not reach the backend. Is the application still starting up?"
    if isinstance(exc, ApiNotFoundError):
        return "The requested item could not be found. It may have been removed."
    if isinstance(exc, ApiValidationError):
        return str(exc)
    if isinstance(exc, ApiConflictError):
        return str(exc)
    if isinstance(exc, ApiServerError):
        return "The backend reported an unexpected error. Check the logs for details."
    return str(exc)


class BaseViewModel(QObject):
    busy_changed = Signal(bool)
    error_occurred = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._busy = False
        self._active_workers: list[_Worker] = []

    @property
    def busy(self) -> bool:
        return self._busy

    def _set_busy(self, value: bool) -> None:
        if self._busy != value:
            self._busy = value
            self.busy_changed.emit(value)

    def run_in_background(
        self,
        fn: Callable[[], Any],
        on_success: Callable[[Any], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        self._set_busy(True)
        worker = _Worker(fn)
        self._active_workers.append(worker)

        def _handle_finished(result: Any) -> None:
            self._active_workers.remove(worker)
            self._set_busy(False)
            if on_success is not None:
                on_success(result)

        def _handle_error(exc: Exception) -> None:
            self._active_workers.remove(worker)
            self._set_busy(False)
            self.error_occurred.emit(format_api_error(exc))
            if on_error is not None:
                on_error(exc)

        worker.signals.finished.connect(_handle_finished)
        worker.signals.error.connect(_handle_error)
        QThreadPool.globalInstance().start(worker)
