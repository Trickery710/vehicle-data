"""Part (inventory catalog item).

``quantity_on_hand`` is a denormalized cache, kept in sync by
``PartRepository.apply_adjustment`` whenever an ``InventoryAdjustment`` is
written -- the exact same "cached column, real log is source of truth"
pattern already used by ``Vehicle.current_mileage``/``MileageRecord``.

``supplier_id`` is only a default/primary-supplier convenience; it is not a
purchasing constraint -- a part can be bought from other suppliers via
individual ``PurchaseOrder.supplier_id`` values.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.inventory_adjustment import InventoryAdjustment
    from backend.app.models.part_compatibility import PartCompatibility
    from backend.app.models.supplier import Supplier


class Part(TimestampMixin, Base):
    __tablename__ = "parts"
    __table_args__ = (
        Index("idx_parts_part_number", "part_number", unique=True),
        Index(
            "idx_parts_barcode",
            "barcode",
            unique=True,
            sqlite_where=text("barcode IS NOT NULL"),
        ),
        Index("idx_parts_supplier_id", "supplier_id"),
        Index("idx_parts_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    part_number: Mapped[str] = mapped_column(String(100), nullable=False)
    oem_number: Mapped[str | None] = mapped_column(String(100))
    aftermarket_number: Mapped[str | None] = mapped_column(String(100))
    barcode: Mapped[str | None] = mapped_column(String(64))

    description: Mapped[str] = mapped_column(String(255), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(150))
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"))

    purchase_cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0, server_default="0")
    retail_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0, server_default="0")
    core_charge: Mapped[float | None] = mapped_column(Numeric(10, 2), default=0, server_default="0")

    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    minimum_stock: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    shelf_location: Mapped[str | None] = mapped_column(String(50))
    warranty_text: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    supplier: Mapped[Supplier | None] = relationship(back_populates="parts")
    compatibility: Mapped[list[PartCompatibility]] = relationship(
        back_populates="part", cascade="all, delete-orphan"
    )
    adjustments: Mapped[list[InventoryAdjustment]] = relationship(
        back_populates="part", order_by="InventoryAdjustment.created_at.desc()"
    )
