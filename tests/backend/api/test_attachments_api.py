"""End-to-end API tests for attachment endpoints (multipart upload/download)."""

from __future__ import annotations


def _create_vehicle(client) -> int:
    r = client.post("/api/v1/customers", json={"first_name": "Jane", "last_name": "Doe"})
    customer_id = r.json()["id"]
    r = client.post(
        "/api/v1/vehicles",
        json={"customer_id": customer_id, "make": "Honda", "skip_vin_decode": True},
    )
    return r.json()["id"]


def test_upload_and_download_round_trip(client) -> None:
    vehicle_id = _create_vehicle(client)
    file_bytes = b"\xff\xd8\xff-fake-jpeg-bytes"

    resp = client.post(
        "/api/v1/attachments",
        files={"file": ("photo.jpg", file_bytes, "image/jpeg")},
        data={
            "entity_type": "vehicle",
            "entity_id": str(vehicle_id),
            "attachment_type": "image",
            "photo_stage": "before",
        },
    )
    assert resp.status_code == 201
    attachment = resp.json()
    assert attachment["file_name"] == "photo.jpg"
    assert attachment["file_size_bytes"] == len(file_bytes)
    assert attachment["photo_stage"] == "before"

    resp = client.get(f"/api/v1/attachments/{attachment['id']}/download")
    assert resp.status_code == 200
    assert resp.content == file_bytes
    assert resp.headers["content-type"] == "image/jpeg"


def test_list_attachments_for_entity(client) -> None:
    vehicle_id = _create_vehicle(client)
    client.post(
        "/api/v1/attachments",
        files={"file": ("a.txt", b"a", "text/plain")},
        data={
            "entity_type": "vehicle",
            "entity_id": str(vehicle_id),
            "attachment_type": "document",
        },
    )
    resp = client.get(
        "/api/v1/attachments", params={"entity_type": "vehicle", "entity_id": vehicle_id}
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_delete_attachment_hard_deletes(client) -> None:
    vehicle_id = _create_vehicle(client)
    resp = client.post(
        "/api/v1/attachments",
        files={"file": ("a.txt", b"a", "text/plain")},
        data={
            "entity_type": "vehicle",
            "entity_id": str(vehicle_id),
            "attachment_type": "document",
        },
    )
    attachment_id = resp.json()["id"]

    resp = client.delete(f"/api/v1/attachments/{attachment_id}")
    assert resp.status_code == 204

    resp = client.get(f"/api/v1/attachments/{attachment_id}")
    assert resp.status_code == 404


def test_get_unknown_attachment_returns_404(client) -> None:
    resp = client.get("/api/v1/attachments/999")
    assert resp.status_code == 404
