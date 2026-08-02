"""Vehicle request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from shared.mechanic_shop_shared.enums import DriveType, FuelType


class VehicleBase(BaseModel):
    vin: str | None = Field(default=None, min_length=17, max_length=17)
    year: int | None = None
    make: str | None = None
    model: str | None = None
    trim: str | None = None
    engine: str | None = None
    transmission: str | None = None
    drive_type: DriveType = DriveType.UNKNOWN
    fuel_type: FuelType = FuelType.UNKNOWN
    license_plate: str | None = None
    license_plate_state: str | None = None
    color: str | None = None
    notes: str | None = None


class VehicleCreate(VehicleBase):
    customer_id: int
    initial_mileage: int | None = Field(default=None, ge=0)
    skip_vin_decode: bool = False


class VehicleUpdate(VehicleBase):
    pass


class VehicleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    vin: str | None
    year: int | None
    make: str | None
    model: str | None
    trim: str | None
    engine: str | None
    transmission: str | None
    drive_type: str
    fuel_type: str
    license_plate: str | None
    license_plate_state: str | None
    color: str | None
    current_mileage: int | None
    notes: str | None
    is_active: bool
    vin_decode_source: str
    vin_decoded_at: datetime | None
    created_at: datetime
    updated_at: datetime


class VinDecodeRequest(BaseModel):
    vin: str = Field(min_length=17, max_length=17)
    allow_online_lookup: bool = True


class VinDecodeResponse(BaseModel):
    vin: str
    is_valid: bool
    source: str
    manufacturer: str | None
    country_of_origin: str | None
    model_year: int | None
    make: str | None
    model: str | None
    trim: str | None
    engine: str | None
    drive_type: str | None
    fuel_type: str | None
    transmission: str | None
    online_lookup_attempted: bool
    online_lookup_succeeded: bool
    warnings: list[str]
