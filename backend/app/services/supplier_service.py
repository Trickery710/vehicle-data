"""Supplier business logic."""

from __future__ import annotations

from backend.app.core.exceptions import NotFoundError
from backend.app.models.supplier import Supplier
from backend.app.repositories.supplier_repository import SupplierRepository
from backend.app.schemas.supplier import SupplierCreate, SupplierUpdate


class SupplierService:
    def __init__(self, supplier_repo: SupplierRepository) -> None:
        self._repo = supplier_repo

    def create_supplier(self, data: SupplierCreate) -> Supplier:
        supplier = Supplier(
            name=data.name,
            contact_name=data.contact_name,
            phone=data.phone,
            email=data.email,
            website=data.website,
            account_number=data.account_number,
            notes=data.notes,
        )
        return self._repo.add(supplier)

    def get_supplier(self, supplier_id: int) -> Supplier:
        supplier = self._repo.get(supplier_id)
        if supplier is None:
            raise NotFoundError(f"Supplier {supplier_id} not found")
        return supplier

    def list_suppliers(self, limit: int = 50, offset: int = 0) -> tuple[list[Supplier], int]:
        return self._repo.list_active(limit=limit, offset=offset)

    def search_suppliers(
        self, query: str, limit: int = 50, offset: int = 0
    ) -> tuple[list[Supplier], int]:
        return self._repo.search(query, limit=limit, offset=offset)

    def update_supplier(self, supplier_id: int, data: SupplierUpdate) -> Supplier:
        supplier = self.get_supplier(supplier_id)
        for field, value in data.model_dump(exclude_unset=True, mode="json").items():
            setattr(supplier, field, value)
        self._repo.db.flush()
        return supplier

    def deactivate_supplier(self, supplier_id: int) -> Supplier:
        supplier = self.get_supplier(supplier_id)
        supplier.is_active = False
        self._repo.db.flush()
        return supplier
