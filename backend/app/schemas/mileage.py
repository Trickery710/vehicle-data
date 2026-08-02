"""Mileage record and vehicle-timeline schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from shared.mechanic_shop_shared.enums import MileageSource


class MileageRecordCreate(BaseModel):
    mileage: int = Field(ge=0)
    source: MileageSource = MileageSource.MANUAL_ENTRY
    notes: str | None = None
    recorded_at: datetime | None = None


class MileageRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mileage: int
    source: str
    notes: str | None
    recorded_at: datetime
    created_at: datetime


class TimelineEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    event_timestamp: datetime
    title: str
    description: str | None
    metadata_json: dict | None
