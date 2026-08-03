"""Tests for PartListViewModel: search and below-minimum-stock filtering."""

from __future__ import annotations

from frontend.mechanic_shop.models.part import Part
from frontend.mechanic_shop.viewmodels.part_list_viewmodel import PartListViewModel


def test_load_populates_table(qtbot, fake_part_client) -> None:
    fake_part_client.parts[1] = Part(id=1, part_number="BRK-001", description="Brake pads")
    viewmodel = PartListViewModel(fake_part_client)

    with qtbot.waitSignal(viewmodel.parts_changed, timeout=1000):
        viewmodel.load()

    assert viewmodel.total == 1
    assert viewmodel.table_model.part_at(0).part_number == "BRK-001"


def test_below_minimum_only_filter(qtbot, fake_part_client) -> None:
    fake_part_client.parts[1] = Part(
        id=1, part_number="LOW-1", description="Low", quantity_on_hand=1, minimum_stock=5
    )
    fake_part_client.parts[2] = Part(
        id=2, part_number="OK-1", description="OK", quantity_on_hand=10, minimum_stock=5
    )
    viewmodel = PartListViewModel(fake_part_client)

    with qtbot.waitSignal(viewmodel.parts_changed, timeout=1000):
        viewmodel.set_below_minimum_only(True)

    assert viewmodel.total == 1
    assert viewmodel.table_model.part_at(0).part_number == "LOW-1"
