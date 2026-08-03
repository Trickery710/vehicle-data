"""End-to-end API tests for part endpoints."""

from __future__ import annotations


def test_create_and_get_part(client) -> None:
    resp = client.post(
        "/api/v1/parts",
        json={
            "part_number": "BRK-001",
            "description": "Brake pads",
            "barcode": "012345678905",
            "purchase_cost": 20,
            "retail_price": 45,
        },
    )
    assert resp.status_code == 201
    part = resp.json()
    assert part["part_number"] == "BRK-001"
    assert part["quantity_on_hand"] == 0

    resp = client.get(f"/api/v1/parts/{part['id']}")
    assert resp.status_code == 200


def test_create_part_duplicate_number_returns_409(client) -> None:
    client.post("/api/v1/parts", json={"part_number": "BRK-001", "description": "Brake pads"})
    resp = client.post("/api/v1/parts", json={"part_number": "BRK-001", "description": "Other"})
    assert resp.status_code == 409


def test_get_part_by_barcode(client) -> None:
    client.post(
        "/api/v1/parts",
        json={"part_number": "BRK-001", "description": "Brake pads", "barcode": "012345678905"},
    )
    resp = client.get("/api/v1/parts/barcode/012345678905")
    assert resp.status_code == 200
    assert resp.json()["part_number"] == "BRK-001"


def test_get_part_by_barcode_unknown_returns_404(client) -> None:
    resp = client.get("/api/v1/parts/barcode/nonexistent")
    assert resp.status_code == 404


def test_update_part(client) -> None:
    part_id = client.post(
        "/api/v1/parts", json={"part_number": "BRK-001", "description": "Brake pads"}
    ).json()["id"]
    resp = client.patch(f"/api/v1/parts/{part_id}", json={"retail_price": 50})
    assert resp.status_code == 200
    assert resp.json()["retail_price"] == 50.0


def test_deactivate_and_reactivate_part(client) -> None:
    part_id = client.post(
        "/api/v1/parts", json={"part_number": "BRK-001", "description": "Brake pads"}
    ).json()["id"]
    resp = client.delete(f"/api/v1/parts/{part_id}")
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    resp = client.post(f"/api/v1/parts/{part_id}/reactivate")
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True


def test_replace_compatibility(client) -> None:
    part_id = client.post(
        "/api/v1/parts", json={"part_number": "BRK-001", "description": "Brake pads"}
    ).json()["id"]
    resp = client.put(
        f"/api/v1/parts/{part_id}/compatibility",
        json=[{"make": "Honda", "model": "Accord", "year_start": 2003, "year_end": 2007}],
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_manual_count_correction_and_adjustments(client) -> None:
    part_id = client.post(
        "/api/v1/parts",
        json={"part_number": "BRK-001", "description": "Brake pads", "initial_quantity_on_hand": 5},
    ).json()["id"]

    resp = client.post(
        f"/api/v1/parts/{part_id}/manual-count-correction",
        json={"quantity_on_hand": 8, "notes": "recount"},
    )
    assert resp.status_code == 200
    assert resp.json()["quantity_delta"] == 3

    resp = client.get(f"/api/v1/parts/{part_id}/adjustments")
    assert resp.status_code == 200
    assert len(resp.json()) == 2  # initial_stock + manual_count_correction


def test_list_parts_filters_below_minimum(client) -> None:
    client.post(
        "/api/v1/parts",
        json={
            "part_number": "LOW-1",
            "description": "Low",
            "initial_quantity_on_hand": 1,
            "minimum_stock": 5,
        },
    )
    client.post(
        "/api/v1/parts",
        json={
            "part_number": "OK-1",
            "description": "OK",
            "initial_quantity_on_hand": 10,
            "minimum_stock": 5,
        },
    )
    resp = client.get("/api/v1/parts", params={"below_minimum_only": True})
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["part_number"] == "LOW-1"


def test_search_parts(client) -> None:
    client.post("/api/v1/parts", json={"part_number": "BRK-001", "description": "Brake pads"})
    client.post("/api/v1/parts", json={"part_number": "OIL-002", "description": "Oil filter"})
    resp = client.get("/api/v1/parts", params={"q": "filter"})
    assert resp.json()["total"] == 1
