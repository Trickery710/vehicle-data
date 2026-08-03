"""Tests for SupplierRepository."""

from __future__ import annotations

from backend.app.models.supplier import Supplier
from backend.app.repositories.supplier_repository import SupplierRepository


def _make_supplier(db, **overrides) -> Supplier:
    defaults = dict(name="NAPA Auto Parts")
    defaults.update(overrides)
    supplier = Supplier(**defaults)
    db.add(supplier)
    db.flush()
    return supplier


def test_list_active_excludes_inactive(db) -> None:
    active = _make_supplier(db, name="NAPA")
    _make_supplier(db, name="Closed Supplier", is_active=False)
    repo = SupplierRepository(db)

    items, total = repo.list_active()
    assert total == 1
    assert items[0].id == active.id


def test_search_matches_name_and_account_number(db) -> None:
    _make_supplier(db, name="NAPA Auto Parts", account_number="ACCT-100")
    _make_supplier(db, name="O'Reilly Auto Parts", account_number="ACCT-200")
    repo = SupplierRepository(db)

    by_name, total = repo.search("NAPA")
    assert total == 1

    by_account, total = repo.search("ACCT-200")
    assert total == 1
    assert by_account[0].name == "O'Reilly Auto Parts"
