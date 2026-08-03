"""Part (inventory) schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PartCompatibilityCreate(BaseModel):
    make: str
    model: str | None = None
    year_start: int | None = None
    year_end: int | None = None
    notes: str | None = None


class PartCompatibilityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    make: str
    model: str | None
    year_start: int | None
    year_end: int | None
    notes: str | None


class PartCreate(BaseModel):
    part_number: str
    oem_number: str | None = None
    aftermarket_number: str | None = None
    barcode: str | None = None
    description: str
    manufacturer: str | None = None
    supplier_id: int | None = None
    purchase_cost: float = Field(default=0, ge=0)
    retail_price: float = Field(default=0, ge=0)
    core_charge: float | None = Field(default=0, ge=0)
    initial_quantity_on_hand: int = Field(default=0, ge=0)
    minimum_stock: int = Field(default=0, ge=0)
    shelf_location: str | None = None
    warranty_text: str | None = None
    compatibility: list[PartCompatibilityCreate] = []


class PartUpdate(BaseModel):
    part_number: str | None = None
    oem_number: str | None = None
    aftermarket_number: str | None = None
    barcode: str | None = None
    description: str | None = None
    manufacturer: str | None = None
    supplier_id: int | None = None
    purchase_cost: float | None = Field(default=None, ge=0)
    retail_price: float | None = Field(default=None, ge=0)
    core_charge: float | None = Field(default=None, ge=0)
    minimum_stock: int | None = Field(default=None, ge=0)
    shelf_location: str | None = None
    warranty_text: str | None = None


class PartRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    part_number: str
    oem_number: str | None
    aftermarket_number: str | None
    barcode: str | None
    description: str
    manufacturer: str | None
    supplier_id: int | None
    purchase_cost: float
    retail_price: float
    core_charge: float | None
    quantity_on_hand: int
    minimum_stock: int
    shelf_location: str | None
    warranty_text: str | None
    is_active: bool
    compatibility: list[PartCompatibilityRead]
    created_at: datetime
    updated_at: datetime


class ManualCountCorrectionRequest(BaseModel):
    quantity_on_hand: int = Field(ge=0)
    notes: str | None = None
