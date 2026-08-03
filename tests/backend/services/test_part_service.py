"""Tests for PartService business rules."""

from __future__ import annotations

import pytest

from backend.app.core.exceptions import ConflictError, NotFoundError
from backend.app.repositories.part_compatibility_repository import PartCompatibilityRepository
from backend.app.repositories.part_repository import PartRepository
from backend.app.schemas.part import (
    ManualCountCorrectionRequest,
    PartCompatibilityCreate,
    PartCreate,
    PartUpdate,
)
from backend.app.services.part_service import PartService


@pytest.fixture()
def service(db) -> PartService:
    return PartService(PartRepository(db), PartCompatibilityRepository(db))


def test_create_part_with_initial_stock_writes_initial_stock_adjustment(
    service: PartService,
) -> None:
    part = service.create_part(
        PartCreate(
            part_number="BRK-001",
            description="Brake pads",
            purchase_cost=20,
            retail_price=45,
            initial_quantity_on_hand=10,
        )
    )
    assert part.quantity_on_hand == 10
    assert len(part.adjustments) == 1
    assert part.adjustments[0].reason == "initial_stock"


def test_create_part_zero_initial_stock_writes_no_adjustment(service: PartService) -> None:
    part = service.create_part(PartCreate(part_number="BRK-001", description="Brake pads"))
    assert part.quantity_on_hand == 0
    assert len(part.adjustments) == 0


def test_create_part_with_compatibility(service: PartService) -> None:
    part = service.create_part(
        PartCreate(
            part_number="BRK-001",
            description="Brake pads",
            compatibility=[
                PartCompatibilityCreate(
                    make="Honda", model="Accord", year_start=2003, year_end=2007
                )
            ],
        )
    )
    assert len(part.compatibility) == 1
    assert part.compatibility[0].make == "Honda"


def test_create_part_duplicate_part_number_raises(service: PartService) -> None:
    service.create_part(PartCreate(part_number="BRK-001", description="Brake pads"))
    with pytest.raises(ConflictError):
        service.create_part(PartCreate(part_number="BRK-001", description="Different pads"))


def test_create_part_duplicate_barcode_raises(service: PartService) -> None:
    service.create_part(PartCreate(part_number="BRK-001", description="Pads", barcode="123456"))
    with pytest.raises(ConflictError):
        service.create_part(
            PartCreate(part_number="OIL-002", description="Filter", barcode="123456")
        )


def test_get_part_unknown_raises(service: PartService) -> None:
    with pytest.raises(NotFoundError):
        service.get_part(999)


def test_update_part_rejects_duplicate_part_number(service: PartService) -> None:
    service.create_part(PartCreate(part_number="BRK-001", description="Brake pads"))
    part2 = service.create_part(PartCreate(part_number="OIL-002", description="Oil filter"))
    with pytest.raises(ConflictError):
        service.update_part(part2.id, PartUpdate(part_number="BRK-001"))


def test_update_part_allows_keeping_own_part_number(service: PartService) -> None:
    part = service.create_part(PartCreate(part_number="BRK-001", description="Brake pads"))
    updated = service.update_part(
        part.id, PartUpdate(part_number="BRK-001", description="New desc")
    )
    assert updated.description == "New desc"


def test_replace_compatibility(service: PartService) -> None:
    from backend.app.models.part_compatibility import PartCompatibility

    part = service.create_part(PartCreate(part_number="BRK-001", description="Brake pads"))
    service.replace_compatibility(part.id, [PartCompatibility(make="Honda", model="Civic")])
    reloaded = service.get_part(part.id)
    assert len(reloaded.compatibility) == 1


def test_record_manual_count_correction_positive_delta(service: PartService) -> None:
    part = service.create_part(
        PartCreate(part_number="BRK-001", description="Brake pads", initial_quantity_on_hand=5)
    )
    adjustment = service.record_manual_count_correction(
        part.id, ManualCountCorrectionRequest(quantity_on_hand=8, notes="recount")
    )
    assert adjustment.quantity_delta == 3
    assert part.quantity_on_hand == 8


def test_record_manual_count_correction_negative_delta(service: PartService) -> None:
    part = service.create_part(
        PartCreate(part_number="BRK-001", description="Brake pads", initial_quantity_on_hand=5)
    )
    adjustment = service.record_manual_count_correction(
        part.id, ManualCountCorrectionRequest(quantity_on_hand=2)
    )
    assert adjustment.quantity_delta == -3
    assert part.quantity_on_hand == 2


def test_deactivate_and_reactivate_part(service: PartService) -> None:
    part = service.create_part(PartCreate(part_number="BRK-001", description="Brake pads"))
    deactivated = service.deactivate_part(part.id)
    assert deactivated.is_active is False

    reactivated = service.reactivate_part(part.id)
    assert reactivated.is_active is True


def test_list_parts_below_minimum_only(service: PartService) -> None:
    service.create_part(
        PartCreate(
            part_number="LOW-1", description="Low", initial_quantity_on_hand=1, minimum_stock=5
        )
    )
    service.create_part(
        PartCreate(
            part_number="OK-1", description="OK", initial_quantity_on_hand=10, minimum_stock=5
        )
    )
    items, total = service.list_parts(below_minimum_only=True)
    assert total == 1
    assert items[0].part_number == "LOW-1"
