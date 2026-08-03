"""InventoryAdjustment schemas -- read-only. Rows are only ever written by
service-layer actions (receiving a PO, selling a part, a manual count
correction, a return) via ``PartRepository.apply_adjustment``, never through
a generic create endpoint.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InventoryAdjustmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    part_id: int
    quantity_delta: int
    quantity_before: int
    quantity_after: int
    reason: str
    repair_order_id: int | None
    purchase_order_id: int | None
    notes: str | None
    created_at: datetime
