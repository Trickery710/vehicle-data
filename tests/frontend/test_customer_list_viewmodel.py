"""Tests for CustomerListViewModel: list loading and debounced search."""

from __future__ import annotations

from frontend.mechanic_shop.models.customer import Customer
from frontend.mechanic_shop.viewmodels.customer_list_viewmodel import CustomerListViewModel


def test_load_populates_table_model(qtbot, fake_customer_client) -> None:
    fake_customer_client.customers[1] = Customer(id=1, first_name="Jane", last_name="Doe")
    viewmodel = CustomerListViewModel(fake_customer_client)

    with qtbot.waitSignal(viewmodel.customers_changed, timeout=1000):
        viewmodel.load()

    assert viewmodel.table_model.rowCount() == 1
    assert viewmodel.table_model.row_at(0).first_name == "Jane"
    assert viewmodel.total == 1


def test_search_debounce_only_calls_api_once_after_rapid_typing(
    qtbot, fake_customer_client
) -> None:
    fake_customer_client.customers[1] = Customer(id=1, first_name="Alice", last_name="Wonderland")
    viewmodel = CustomerListViewModel(fake_customer_client)

    # Simulate rapid keystrokes -- each call restarts the debounce timer, so
    # only the last one should ever reach the API.
    for partial in ["A", "Al", "Ali", "Alic", "Alice"]:
        viewmodel.set_search_query(partial)
        qtbot.wait(30)  # faster than the 300ms debounce interval

    with qtbot.waitSignal(viewmodel.customers_changed, timeout=1000):
        pass

    assert fake_customer_client.list_calls == ["Alice"]
    assert viewmodel.total == 1


def test_deactivate_customer_refreshes_list(qtbot, fake_customer_client) -> None:
    fake_customer_client.customers[1] = Customer(id=1, first_name="Jane", last_name="Doe")
    viewmodel = CustomerListViewModel(fake_customer_client)

    done = {"called": False}

    def on_done() -> None:
        done["called"] = True

    with qtbot.waitSignal(viewmodel.customers_changed, timeout=1000):
        viewmodel.deactivate_customer(1, on_done=on_done)

    assert done["called"] is True
    assert fake_customer_client.customers[1].is_active is False
