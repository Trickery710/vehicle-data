"""Client-side Part (inventory), PartCompatibility, and InventoryAdjustment
data shapes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PartCompatibility:
    id: int | None
    make: str
    model: str | None = None
    year_start: int | None = None
    year_end: int | None = None
    notes: str | None = None

    @classmethod
    def from_api(cls, data: dict) -> PartCompatibility:
        return cls(
            id=data.get("id"),
            make=data["make"],
            model=data.get("model"),
            year_start=data.get("year_start"),
            year_end=data.get("year_end"),
            notes=data.get("notes"),
        )

    def to_create_payload(self) -> dict:
        return {
            "make": self.make,
            "model": self.model,
            "year_start": self.year_start,
            "year_end": self.year_end,
            "notes": self.notes,
        }


@dataclass
class InventoryAdjustment:
    id: int
    part_id: int
    quantity_delta: int
    quantity_before: int
    quantity_after: int
    reason: str
    repair_order_id: int | None
    purchase_order_id: int | None
    notes: str | None
    created_at: datetime | None

    @classmethod
    def from_api(cls, data: dict) -> InventoryAdjustment:
        return cls(
            id=data["id"],
            part_id=data["part_id"],
            quantity_delta=data["quantity_delta"],
            quantity_before=data["quantity_before"],
            quantity_after=data["quantity_after"],
            reason=data["reason"],
            repair_order_id=data.get("repair_order_id"),
            purchase_order_id=data.get("purchase_order_id"),
            notes=data.get("notes"),
            created_at=_parse_datetime(data.get("created_at")),
        )


@dataclass
class Part:
    id: int | None
    part_number: str
    oem_number: str | None = None
    aftermarket_number: str | None = None
    barcode: str | None = None
    description: str = ""
    manufacturer: str | None = None
    supplier_id: int | None = None
    purchase_cost: float = 0
    retail_price: float = 0
    core_charge: float | None = 0
    quantity_on_hand: int = 0
    minimum_stock: int = 0
    shelf_location: str | None = None
    warranty_text: str | None = None
    is_active: bool = True
    compatibility: list[PartCompatibility] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_below_minimum(self) -> bool:
        return self.quantity_on_hand < self.minimum_stock

    @classmethod
    def from_api(cls, data: dict) -> Part:
        return cls(
            id=data.get("id"),
            part_number=data["part_number"],
            oem_number=data.get("oem_number"),
            aftermarket_number=data.get("aftermarket_number"),
            barcode=data.get("barcode"),
            description=data.get("description", ""),
            manufacturer=data.get("manufacturer"),
            supplier_id=data.get("supplier_id"),
            purchase_cost=data.get("purchase_cost", 0),
            retail_price=data.get("retail_price", 0),
            core_charge=data.get("core_charge", 0),
            quantity_on_hand=data.get("quantity_on_hand", 0),
            minimum_stock=data.get("minimum_stock", 0),
            shelf_location=data.get("shelf_location"),
            warranty_text=data.get("warranty_text"),
            is_active=data.get("is_active", True),
            compatibility=[PartCompatibility.from_api(c) for c in data.get("compatibility", [])],
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")),
        )

    def to_create_payload(self, initial_quantity_on_hand: int = 0) -> dict:
        return {
            "part_number": self.part_number,
            "oem_number": self.oem_number,
            "aftermarket_number": self.aftermarket_number,
            "barcode": self.barcode,
            "description": self.description,
            "manufacturer": self.manufacturer,
            "supplier_id": self.supplier_id,
            "purchase_cost": self.purchase_cost,
            "retail_price": self.retail_price,
            "core_charge": self.core_charge,
            "initial_quantity_on_hand": initial_quantity_on_hand,
            "minimum_stock": self.minimum_stock,
            "shelf_location": self.shelf_location,
            "warranty_text": self.warranty_text,
            "compatibility": [c.to_create_payload() for c in self.compatibility],
        }

    def to_update_payload(self) -> dict:
        return {
            "part_number": self.part_number,
            "oem_number": self.oem_number,
            "aftermarket_number": self.aftermarket_number,
            "barcode": self.barcode,
            "description": self.description,
            "manufacturer": self.manufacturer,
            "supplier_id": self.supplier_id,
            "purchase_cost": self.purchase_cost,
            "retail_price": self.retail_price,
            "core_charge": self.core_charge,
            "minimum_stock": self.minimum_stock,
            "shelf_location": self.shelf_location,
            "warranty_text": self.warranty_text,
        }


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
