"""Phone number request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from shared.mechanic_shop_shared.enums import PhoneType


class PhoneNumberCreate(BaseModel):
    phone_number: str
    phone_type: PhoneType = PhoneType.MOBILE
    is_primary: bool = False
    extension: str | None = None


class PhoneNumberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    phone_number: str
    phone_type: str
    is_primary: bool
    extension: str | None
    created_at: datetime
    updated_at: datetime
