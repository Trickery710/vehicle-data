"""Supplier schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SupplierCreate(BaseModel):
    name: str
    contact_name: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    account_number: str | None = None
    notes: str | None = None


class SupplierUpdate(BaseModel):
    name: str | None = None
    contact_name: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    account_number: str | None = None
    notes: str | None = None


class SupplierRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    contact_name: str | None
    phone: str | None
    email: str | None
    website: str | None
    account_number: str | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
