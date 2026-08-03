"""Tests for DiagnosticSessionDetailViewModel: mirrors
EstimateDetailViewModel's "create unlocks in place" test pattern."""

from __future__ import annotations

from frontend.mechanic_shop.models.diagnostic import (
    DiagnosticReading,
    DiagnosticSession,
    DiagnosticTroubleCode,
)
from frontend.mechanic_shop.viewmodels.diagnostic_session_detail_viewmodel import (
    DiagnosticSessionDetailViewModel,
)


def test_save_new_session_calls_create(qtbot, fake_diagnostic_client) -> None:
    viewmodel = DiagnosticSessionDetailViewModel(fake_diagnostic_client, vehicle_id=1)
    viewmodel.session.summary = "Check engine light"

    with qtbot.waitSignal(viewmodel.saved, timeout=1000):
        viewmodel.save()

    assert viewmodel.session.id is not None
    assert viewmodel.is_new is False
    assert fake_diagnostic_client.sessions[viewmodel.session.id].summary == "Check engine light"


def test_load_existing_session(qtbot, fake_diagnostic_client) -> None:
    fake_diagnostic_client.sessions[1] = DiagnosticSession(
        id=1, vehicle_id=1, summary="Existing session"
    )
    viewmodel = DiagnosticSessionDetailViewModel(fake_diagnostic_client, vehicle_id=1, session_id=1)

    with qtbot.waitSignal(viewmodel.session_loaded, timeout=1000):
        viewmodel.load()

    assert viewmodel.session.summary == "Existing session"


def test_replace_trouble_codes(qtbot, fake_diagnostic_client) -> None:
    fake_diagnostic_client.sessions[1] = DiagnosticSession(id=1, vehicle_id=1)
    viewmodel = DiagnosticSessionDetailViewModel(fake_diagnostic_client, vehicle_id=1, session_id=1)

    new_codes = [DiagnosticTroubleCode(id=None, code="P0301")]
    with qtbot.waitSignal(viewmodel.session_loaded, timeout=1000):
        viewmodel.replace_trouble_codes(new_codes)

    assert viewmodel.session.trouble_codes == new_codes


def test_replace_readings(qtbot, fake_diagnostic_client) -> None:
    fake_diagnostic_client.sessions[1] = DiagnosticSession(id=1, vehicle_id=1)
    viewmodel = DiagnosticSessionDetailViewModel(fake_diagnostic_client, vehicle_id=1, session_id=1)

    new_readings = [DiagnosticReading(id=None, reading_type="compression", label="Cylinder 1")]
    with qtbot.waitSignal(viewmodel.session_loaded, timeout=1000):
        viewmodel.replace_readings(new_readings)

    assert viewmodel.session.readings == new_readings
