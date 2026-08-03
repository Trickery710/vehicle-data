"""End-to-end API tests for diagnostic session endpoints."""

from __future__ import annotations


def _create_vehicle(client) -> int:
    customer_id = client.post(
        "/api/v1/customers", json={"first_name": "Jane", "last_name": "Doe"}
    ).json()["id"]
    return client.post(
        "/api/v1/vehicles",
        json={"customer_id": customer_id, "make": "Honda", "skip_vin_decode": True},
    ).json()["id"]


def test_create_diagnostic_session_with_codes_and_readings(client) -> None:
    vehicle_id = _create_vehicle(client)
    resp = client.post(
        "/api/v1/diagnostic-sessions",
        json={
            "vehicle_id": vehicle_id,
            "mileage_at_time": 55000,
            "summary": "Check engine light",
            "trouble_codes": [{"code": "P0301", "description": "Cylinder 1 misfire"}],
            "readings": [
                {"reading_type": "compression", "label": "Cylinder 1", "value": 150, "unit": "psi"}
            ],
        },
    )
    assert resp.status_code == 201
    session = resp.json()
    assert len(session["trouble_codes"]) == 1
    assert len(session["readings"]) == 1

    vehicle = client.get(f"/api/v1/vehicles/{vehicle_id}").json()
    assert vehicle["current_mileage"] == 55000


def test_create_diagnostic_session_unknown_vehicle_returns_404(client) -> None:
    resp = client.post("/api/v1/diagnostic-sessions", json={"vehicle_id": 999})
    assert resp.status_code == 404


def test_update_diagnostic_session(client) -> None:
    vehicle_id = _create_vehicle(client)
    session_id = client.post("/api/v1/diagnostic-sessions", json={"vehicle_id": vehicle_id}).json()[
        "id"
    ]
    resp = client.patch(
        f"/api/v1/diagnostic-sessions/{session_id}", json={"summary": "Updated summary"}
    )
    assert resp.status_code == 200
    assert resp.json()["summary"] == "Updated summary"


def test_replace_trouble_codes(client) -> None:
    vehicle_id = _create_vehicle(client)
    session_id = client.post("/api/v1/diagnostic-sessions", json={"vehicle_id": vehicle_id}).json()[
        "id"
    ]
    resp = client.put(
        f"/api/v1/diagnostic-sessions/{session_id}/trouble-codes",
        json=[{"code": "P0420", "code_type": "obd2", "status": "stored"}],
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_replace_readings(client) -> None:
    vehicle_id = _create_vehicle(client)
    session_id = client.post("/api/v1/diagnostic-sessions", json={"vehicle_id": vehicle_id}).json()[
        "id"
    ]
    resp = client.put(
        f"/api/v1/diagnostic-sessions/{session_id}/readings",
        json=[{"reading_type": "battery_test", "label": "Battery", "value": 12.6, "unit": "V"}],
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_vehicle_scoped_diagnostic_sessions_list(client) -> None:
    vehicle_id = _create_vehicle(client)
    client.post("/api/v1/diagnostic-sessions", json={"vehicle_id": vehicle_id})
    resp = client.get(f"/api/v1/vehicles/{vehicle_id}/diagnostic-sessions")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
