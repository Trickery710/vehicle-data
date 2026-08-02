"""Estimate schemas.

Line items are not nested in ``EstimateRead`` -- ``LineItem`` is polymorphic
(entity_type/entity_id), not a direct ORM relationship, so it's fetched via
its own endpoint (``GET/PUT /estimates/{id}/line-items``), matching how
``GET /vehicles/{id}/timeline`` is already its own endpoint rather than
nested in ``VehicleRead``.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.app.schemas.line_item import LineItemCreate


class EstimateCreate(BaseModel):
    vehicle_id: int
    title: str | None = None
    notes: str | None = None
    line_items: list[LineItemCreate] = []


class EstimateUpdate(BaseModel):
    title: str | None = None
    notes: str | None = None


class EstimateApproveRequest(BaseModel):
    signer_name: str | None = None


class EstimateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    estimate_number: str
    vehicle_id: int
    customer_id: int
    status: str
    title: str | None
    notes: str | None
    sent_at: datetime | None
    approved_at: datetime | None
    declined_at: datetime | None
    converted_at: datetime | None
    created_at: datetime
    updated_at: datetime
