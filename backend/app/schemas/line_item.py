"""Line item schemas, shared by Estimate/RepairOrder/Invoice schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from shared.mechanic_shop_shared.enums import LineItemType


class LineItemCreate(BaseModel):
    line_type: LineItemType = LineItemType.PART
    description: str
    quantity: float = Field(default=1, gt=0)
    unit_price: float = 0
    is_taxable: bool = True
    part_number: str | None = None
    part_id: int | None = None
    warranty_text: str | None = None
    sort_order: int = 0


class LineItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    line_type: str
    description: str
    quantity: float
    unit_price: float
    is_taxable: bool
    part_number: str | None
    part_id: int | None
    warranty_text: str | None
    sort_order: int
    line_total: float
