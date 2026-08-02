"""End-to-end API tests for vehicle endpoints. Network (vPIC) is mocked via respx."""

from __future__ import annotations

import httpx
import respx

from backend.app.vin.vpic_client import _VPIC_BASE_URL

VALID_NA_VIN = "1HGCM82633A004352"


def _create_customer(client) -> int:
    resp = client.post("/api/v1/customers", json={"first_name": "Jane", "last_name": "Doe"})
    return resp.json()["id"]


def test_create_vehicle_without_vin(client) -> None:
    customer_id = _create_customer(client)
    resp = client.post(
        "/api/v1/vehicles",
        json={"customer_id": customer_id, "make": "Honda", "model": "Accord", "year": 2003},
    )
    assert resp.status_code == 201
    assert resp.json()["make"] == "Honda"


def test_create_vehicle_unknown_customer_returns_404(client) -> None:
    resp = client.post("/api/v1/vehicles", json={"customer_id": 999, "skip_vin_decode": True})
    assert resp.status_code == 404


@respx.mock
def test_create_vehicle_with_vin_decodes_offline_and_online(client) -> None:
    respx.get(f"{_VPIC_BASE_URL}/{VALID_NA_VIN}").mock(
        return_value=httpx.Response(
            200, json={"Results": [{"Make": "HONDA", "Model": "Accord", "ModelYear": "2003"}]}
        )
    )
    customer_id = _create_customer(client)
    resp = client.post("/api/v1/vehicles", json={"customer_id": customer_id, "vin": VALID_NA_VIN})
    assert resp.status_code == 201
    body = resp.json()
    assert body["year"] == 2003
    assert body["make"] == "HONDA"
    assert body["vin_decode_source"] == "vpic"


def test_duplicate_vin_returns_409(client) -> None:
    customer_id = _create_customer(client)
    client.post(
        "/api/v1/vehicles",
        json={"customer_id": customer_id, "vin": VALID_NA_VIN, "skip_vin_decode": True},
    )
    resp = client.post(
        "/api/v1/vehicles",
        json={"customer_id": customer_id, "vin": VALID_NA_VIN, "skip_vin_decode": True},
    )
    assert resp.status_code == 409


@respx.mock
def test_vin_decode_preview_endpoint_has_no_side_effects(client) -> None:
    respx.get(f"{_VPIC_BASE_URL}/{VALID_NA_VIN}").mock(side_effect=httpx.ConnectError("offline"))
    resp = client.post("/api/v1/vehicles/vin-decode", json={"vin": VALID_NA_VIN})
    assert resp.status_code == 200
    body = resp.json()
    assert body["model_year"] == 2003
    assert body["online_lookup_succeeded"] is False
    assert any("Online decode unavailable" in w for w in body["warnings"])

    # No vehicle was created by the preview.
    resp = client.get("/api/v1/vehicles")
    assert resp.json()["total"] == 0


def test_vin_decode_invalid_vin_returns_422(client) -> None:
    resp = client.post("/api/v1/vehicles/vin-decode", json={"vin": "TOO_SHORT"})
    assert resp.status_code == 422


def test_add_mileage_and_get_timeline(client) -> None:
    customer_id = _create_customer(client)
    create = client.post(
        "/api/v1/vehicles",
        json={"customer_id": customer_id, "skip_vin_decode": True, "initial_mileage": 10000},
    )
    vehicle_id = create.json()["id"]

    resp = client.post(f"/api/v1/vehicles/{vehicle_id}/mileage", json={"mileage": 10500})
    assert resp.status_code == 200
    assert resp.json()["current_mileage"] == 10500

    resp = client.get(f"/api/v1/vehicles/{vehicle_id}/timeline")
    assert resp.status_code == 200
    event_types = {e["event_type"] for e in resp.json()}
    assert "vehicle_created" in event_types
    assert "mileage_updated" in event_types


def test_search_vehicles_by_license_plate(client) -> None:
    customer_id = _create_customer(client)
    client.post(
        "/api/v1/vehicles",
        json={"customer_id": customer_id, "license_plate": "ABC123", "skip_vin_decode": True},
    )
    resp = client.get("/api/v1/vehicles", params={"q": "ABC123"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_deactivate_vehicle_is_soft_delete(client) -> None:
    customer_id = _create_customer(client)
    create = client.post(
        "/api/v1/vehicles", json={"customer_id": customer_id, "skip_vin_decode": True}
    )
    vehicle_id = create.json()["id"]

    resp = client.delete(f"/api/v1/vehicles/{vehicle_id}")
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False
