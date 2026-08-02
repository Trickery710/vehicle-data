"""Tests for VehicleDetailViewModel: VIN decode debounce/apply, save routing."""

from __future__ import annotations

from frontend.mechanic_shop.models.vehicle import Vehicle, VinDecodeResult
from frontend.mechanic_shop.viewmodels.vehicle_detail_viewmodel import VehicleDetailViewModel

VALID_VIN = "1HGCM82633A004352"


def _decode_result(**overrides) -> VinDecodeResult:
    defaults = dict(
        vin=VALID_VIN,
        is_valid=True,
        source="vpic",
        manufacturer="Honda (USA)",
        country_of_origin="USA",
        model_year=2003,
        make="HONDA",
        model="Accord",
        trim="EX-V6",
        engine="3.0L V6",
        drive_type="fwd",
        fuel_type="gasoline",
        transmission="Automatic",
        online_lookup_attempted=True,
        online_lookup_succeeded=True,
        warnings=[],
    )
    defaults.update(overrides)
    return VinDecodeResult(**defaults)


def test_vin_text_change_debounces_then_decodes(qtbot, fake_vehicle_client) -> None:
    fake_vehicle_client.canned_decode_result = _decode_result()
    viewmodel = VehicleDetailViewModel(fake_vehicle_client, customer_id=1)

    # Simulate keystrokes typing out the VIN one character at a time --
    # only a full 17-char VIN should ever trigger a decode call.
    for i in range(1, len(VALID_VIN)):
        viewmodel.on_vin_text_changed(VALID_VIN[:i])
    assert fake_vehicle_client.decode_calls == []

    with qtbot.waitSignal(viewmodel.vin_decoded, timeout=1000):
        viewmodel.on_vin_text_changed(VALID_VIN)

    assert fake_vehicle_client.decode_calls == [VALID_VIN]
    assert viewmodel.last_vin_decode.make == "HONDA"


def test_apply_decoded_vin_result_fills_blank_fields_only(qtbot, fake_vehicle_client) -> None:
    fake_vehicle_client.canned_decode_result = _decode_result(make="HONDA", model="Accord")
    viewmodel = VehicleDetailViewModel(fake_vehicle_client, customer_id=1)
    viewmodel.vehicle.make = "Custom Make"  # user already typed something

    with qtbot.waitSignal(viewmodel.vin_decoded, timeout=1000):
        viewmodel.on_vin_text_changed(VALID_VIN)

    viewmodel.apply_decoded_vin_result()

    assert viewmodel.vehicle.make == "Custom Make"  # not overwritten
    assert viewmodel.vehicle.model == "Accord"  # was blank, now filled
    assert viewmodel.vehicle.year == 2003


def test_save_new_vehicle_calls_create(qtbot, fake_vehicle_client) -> None:
    viewmodel = VehicleDetailViewModel(fake_vehicle_client, customer_id=7)
    viewmodel.vehicle.make = "Honda"
    viewmodel.set_initial_mileage(1000)

    with qtbot.waitSignal(viewmodel.saved, timeout=1000):
        viewmodel.save()

    assert len(fake_vehicle_client.create_calls) == 1
    assert fake_vehicle_client.create_calls[0].make == "Honda"
    assert viewmodel.vehicle.id is not None
    assert viewmodel.is_new is False


def test_save_existing_vehicle_calls_update(qtbot, fake_vehicle_client) -> None:
    fake_vehicle_client.vehicles[5] = Vehicle(id=5, customer_id=7, make="Honda")
    viewmodel = VehicleDetailViewModel(fake_vehicle_client, customer_id=7, vehicle_id=5)

    with qtbot.waitSignal(viewmodel.vehicle_loaded, timeout=1000):
        viewmodel.load()

    viewmodel.vehicle.color = "Blue"
    with qtbot.waitSignal(viewmodel.saved, timeout=1000):
        viewmodel.save()

    assert len(fake_vehicle_client.update_calls) == 1
    updated_id, updated_vehicle = fake_vehicle_client.update_calls[0]
    assert updated_id == 5
    assert updated_vehicle.color == "Blue"
    assert fake_vehicle_client.create_calls == []


def test_add_mileage_reading_updates_vehicle(qtbot, fake_vehicle_client) -> None:
    fake_vehicle_client.vehicles[5] = Vehicle(id=5, customer_id=7, current_mileage=100)
    viewmodel = VehicleDetailViewModel(fake_vehicle_client, customer_id=7, vehicle_id=5)

    with qtbot.waitSignal(viewmodel.vehicle_loaded, timeout=1000):
        viewmodel.load()

    with qtbot.waitSignal(viewmodel.vehicle_loaded, timeout=1000):
        viewmodel.add_mileage_reading(500)

    assert viewmodel.vehicle.current_mileage == 500
