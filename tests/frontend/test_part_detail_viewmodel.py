"""Tests for PartDetailViewModel: create/edit, compatibility, adjustment history."""

from __future__ import annotations

from frontend.mechanic_shop.models.part import Part, PartCompatibility
from frontend.mechanic_shop.viewmodels.part_detail_viewmodel import PartDetailViewModel


def test_save_new_part_with_initial_quantity(qtbot, fake_part_client) -> None:
    viewmodel = PartDetailViewModel(fake_part_client)
    viewmodel.part.part_number = "BRK-001"
    viewmodel.part.description = "Brake pads"
    viewmodel.initial_quantity_on_hand = 10

    with qtbot.waitSignal(viewmodel.saved, timeout=1000):
        viewmodel.save()

    assert viewmodel.part.id is not None
    assert fake_part_client.parts[viewmodel.part.id].quantity_on_hand == 10


def test_load_existing_part_and_adjustments(qtbot, fake_part_client) -> None:
    fake_part_client.parts[1] = Part(id=1, part_number="BRK-001", description="Brake pads")
    viewmodel = PartDetailViewModel(fake_part_client, part_id=1)

    with qtbot.waitSignal(viewmodel.adjustments_loaded, timeout=1000):
        viewmodel.load()

    assert viewmodel.part.part_number == "BRK-001"


def test_replace_compatibility(qtbot, fake_part_client) -> None:
    fake_part_client.parts[1] = Part(id=1, part_number="BRK-001", description="Brake pads")
    viewmodel = PartDetailViewModel(fake_part_client, part_id=1)

    new_compat = [PartCompatibility(id=None, make="Honda", model="Accord")]
    with qtbot.waitSignal(viewmodel.part_loaded, timeout=1000):
        viewmodel.replace_compatibility(new_compat)

    assert viewmodel.part.compatibility == new_compat


def test_record_manual_count_correction_reloads_part(qtbot, fake_part_client) -> None:
    fake_part_client.parts[1] = Part(
        id=1, part_number="BRK-001", description="Brake pads", quantity_on_hand=5
    )
    fake_part_client.adjustments[1] = []
    viewmodel = PartDetailViewModel(fake_part_client, part_id=1)

    with qtbot.waitSignal(viewmodel.part_loaded, timeout=1000):
        viewmodel.record_manual_count_correction(8, notes="recount")

    assert viewmodel.part.quantity_on_hand == 8


def test_deactivate_and_reactivate(qtbot, fake_part_client) -> None:
    fake_part_client.parts[1] = Part(id=1, part_number="BRK-001", description="Brake pads")
    viewmodel = PartDetailViewModel(fake_part_client, part_id=1)

    with qtbot.waitSignal(viewmodel.part_loaded, timeout=1000):
        viewmodel.deactivate()
    assert viewmodel.part.is_active is False

    with qtbot.waitSignal(viewmodel.part_loaded, timeout=1000):
        viewmodel.reactivate()
    assert viewmodel.part.is_active is True
