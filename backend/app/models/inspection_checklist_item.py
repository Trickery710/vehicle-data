"""Inspection checklist item, always owned by exactly one RepairOrder.

Direct FK (not polymorphic) since checklist items never belong to anything
else. Fully ad-hoc for Phase 2 -- no checklist-template table -- but
template-ready: a future "create from template" feature would just be a
service method bulk-inserting rows here, no schema change needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.repair_order import RepairOrder


class InspectionChecklistItem(TimestampMixin, Base):
    __tablename__ = "inspection_checklist_items"
    __table_args__ = (Index("idx_inspection_checklist_items_repair_order_id", "repair_order_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    repair_order_id: Mapped[int] = mapped_column(
        ForeignKey("repair_orders.id", ondelete="CASCADE"), nullable=False
    )

    item_description: Mapped[str] = mapped_column(String(255), nullable=False)
    result: Mapped[str | None] = mapped_column(String(10))  # pass|fail|na; None = not yet checked
    notes: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    repair_order: Mapped[RepairOrder] = relationship(back_populates="checklist_items")
