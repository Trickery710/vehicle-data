"""Tests for CustomerRepository against a real (temp) SQLite database."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.models.customer import Customer
from backend.app.models.phone_number import PhoneNumber
from backend.app.repositories.customer_repository import CustomerRepository


def _make_customer(db, **overrides) -> Customer:
    defaults = dict(first_name="Jane", last_name="Doe", email="jane@example.com")
    defaults.update(overrides)
    customer = Customer(**defaults)
    db.add(customer)
    db.flush()
    return customer


def test_add_and_get(db) -> None:
    repo = CustomerRepository(db)
    customer = _make_customer(db)
    fetched = repo.get(customer.id)
    assert fetched is not None
    assert fetched.email == "jane@example.com"


def test_cascade_deletes_phone_numbers(db) -> None:
    repo = CustomerRepository(db)
    customer = _make_customer(db)
    db.add(PhoneNumber(customer_id=customer.id, phone_number="555-1111", is_primary=True))
    db.flush()

    repo.delete(customer)
    db.flush()

    remaining = db.query(PhoneNumber).filter_by(customer_id=customer.id).all()
    assert remaining == []


def test_only_one_primary_phone_enforced_by_partial_unique_index(db) -> None:
    customer = _make_customer(db)
    db.add(PhoneNumber(customer_id=customer.id, phone_number="555-1111", is_primary=True))
    db.flush()
    db.add(PhoneNumber(customer_id=customer.id, phone_number="555-2222", is_primary=True))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()  # required before the session can be used/committed again


def test_search_matches_name_email_and_phone(db) -> None:
    repo = CustomerRepository(db)
    c1 = _make_customer(db, first_name="Alice", last_name="Smith", email="alice@example.com")
    db.add(PhoneNumber(customer_id=c1.id, phone_number="555-9999", is_primary=True))
    _make_customer(db, first_name="Bob", last_name="Jones", email="bob@example.com")
    db.flush()

    by_name, total = repo.search("Alice")
    assert total == 1
    assert by_name[0].id == c1.id

    by_phone, total = repo.search("9999")
    assert total == 1
    assert by_phone[0].id == c1.id


def test_list_active_excludes_inactive(db) -> None:
    repo = CustomerRepository(db)
    _make_customer(db, first_name="Active")
    _make_customer(db, first_name="Inactive", is_active=False)

    items, total = repo.list_active()
    assert total == 1
    assert items[0].first_name == "Active"


def test_business_name_only_customer_is_valid(db) -> None:
    repo = CustomerRepository(db)
    customer = _make_customer(db, first_name=None, last_name=None, business_name="Joe's Garage")
    fetched = repo.get(customer.id)
    assert fetched.business_name == "Joe's Garage"
