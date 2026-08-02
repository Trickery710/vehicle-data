"""Vehicle detail view: create/edit a vehicle, VIN decode, mileage, and history."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.viewmodels.vehicle_detail_viewmodel import VehicleDetailViewModel
from frontend.mechanic_shop.views.widgets.vin_input_widget import VinInputWidget
from shared.mechanic_shop_shared.enums import DriveType, FuelType

_MAX_MILEAGE = 2_000_000


class VehicleDetailView(QWidget):
    closed = Signal()
    saved = Signal(int)

    def __init__(self, viewmodel: VehicleDetailViewModel) -> None:
        super().__init__()
        self.viewmodel = viewmodel

        layout = QVBoxLayout(self)

        header_row = QHBoxLayout()
        back_button = QPushButton("< Back")
        back_button.clicked.connect(self.closed.emit)
        header_row.addWidget(back_button)
        header_row.addStretch(1)
        layout.addLayout(header_row)

        heading_text = "New Vehicle" if viewmodel.is_new else "Edit Vehicle"
        self._heading = QLabel(heading_text)
        self._heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(self._heading)

        self._vin_widget = VinInputWidget()
        self._vin_widget.vin_text_changed.connect(self.viewmodel.on_vin_text_changed)
        self._vin_widget.apply_decoded_result_requested.connect(self._on_apply_decoded_result)
        layout.addWidget(self._vin_widget)

        form = QFormLayout()
        self._year = QSpinBox()
        self._year.setRange(0, 2100)
        self._make = QLineEdit()
        self._model = QLineEdit()
        self._trim = QLineEdit()
        self._engine = QLineEdit()
        self._transmission = QLineEdit()
        self._drive_type = QComboBox()
        self._drive_type.addItems([d.value for d in DriveType])
        self._fuel_type = QComboBox()
        self._fuel_type.addItems([f.value for f in FuelType])
        self._license_plate = QLineEdit()
        self._license_plate_state = QLineEdit()
        self._license_plate_state.setMaxLength(2)
        self._color = QLineEdit()
        self._notes = QTextEdit()
        self._notes.setFixedHeight(80)

        form.addRow("Year", self._year)
        form.addRow("Make", self._make)
        form.addRow("Model", self._model)
        form.addRow("Trim", self._trim)
        form.addRow("Engine", self._engine)
        form.addRow("Transmission", self._transmission)
        form.addRow("Drive Type", self._drive_type)
        form.addRow("Fuel Type", self._fuel_type)
        form.addRow("License Plate", self._license_plate)
        form.addRow("Plate State", self._license_plate_state)
        form.addRow("Color", self._color)
        form.addRow("Notes", self._notes)
        layout.addLayout(form)

        mileage_row = QHBoxLayout()
        self._mileage_label = QLabel("Current Mileage: --")
        mileage_row.addWidget(self._mileage_label)
        self._mileage_input = QSpinBox()
        self._mileage_input.setRange(0, _MAX_MILEAGE)
        mileage_row.addWidget(self._mileage_input)
        self._mileage_button = QPushButton("Record Reading")
        self._mileage_button.clicked.connect(self._on_record_mileage)
        mileage_row.addWidget(self._mileage_button)
        layout.addLayout(mileage_row)
        self._mileage_input.setEnabled(not viewmodel.is_new)
        self._mileage_button.setEnabled(not viewmodel.is_new)
        if viewmodel.is_new:
            self._mileage_label.setText("Initial Mileage (optional)")
            self._mileage_button.setText("(set on save)")
            self._mileage_button.setEnabled(False)

        layout.addWidget(QLabel("Vehicle History"))
        self._timeline_list = QListWidget()
        layout.addWidget(self._timeline_list)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self._save_button = QPushButton("Save Vehicle")
        self._save_button.setObjectName("primaryButton")
        self._save_button.clicked.connect(self._on_save_clicked)
        button_row.addWidget(self._save_button)
        layout.addLayout(button_row)

        self.viewmodel.vehicle_loaded.connect(self._on_vehicle_loaded)
        self.viewmodel.timeline_loaded.connect(self._on_timeline_loaded)
        self.viewmodel.vin_decoded.connect(self._vin_widget.show_decode_result)
        self.viewmodel.saved.connect(self._on_saved)
        self.viewmodel.error_occurred.connect(self._on_error)
        self.viewmodel.busy_changed.connect(self._save_button.setDisabled)

    def load(self) -> None:
        self.viewmodel.load()

    def _on_vehicle_loaded(self) -> None:
        vehicle = self.viewmodel.vehicle
        self._vin_widget.set_vin_text(vehicle.vin or "")
        self._year.setValue(vehicle.year or 0)
        self._make.setText(vehicle.make or "")
        self._model.setText(vehicle.model or "")
        self._trim.setText(vehicle.trim or "")
        self._engine.setText(vehicle.engine or "")
        self._transmission.setText(vehicle.transmission or "")
        self._drive_type.setCurrentText(vehicle.drive_type)
        self._fuel_type.setCurrentText(vehicle.fuel_type)
        self._license_plate.setText(vehicle.license_plate or "")
        self._license_plate_state.setText(vehicle.license_plate_state or "")
        self._color.setText(vehicle.color or "")
        self._notes.setPlainText(vehicle.notes or "")
        if not self.viewmodel.is_new:
            mileage_text = (
                f"{vehicle.current_mileage:,}" if vehicle.current_mileage is not None else "--"
            )
            self._mileage_label.setText(f"Current Mileage: {mileage_text}")

    def _on_timeline_loaded(self) -> None:
        self._timeline_list.clear()
        for event in self.viewmodel.timeline:
            timestamp = (
                event.event_timestamp.strftime("%Y-%m-%d %H:%M") if event.event_timestamp else ""
            )
            self._timeline_list.addItem(QListWidgetItem(f"{timestamp} -- {event.title}"))

    def _on_apply_decoded_result(self) -> None:
        self.viewmodel.apply_decoded_vin_result()
        self._on_vehicle_loaded()  # re-render the form with the newly-filled fields

    def _collect_form_into_viewmodel(self) -> None:
        vehicle = self.viewmodel.vehicle
        vehicle.year = self._year.value() or None
        vehicle.make = self._make.text().strip() or None
        vehicle.model = self._model.text().strip() or None
        vehicle.trim = self._trim.text().strip() or None
        vehicle.engine = self._engine.text().strip() or None
        vehicle.transmission = self._transmission.text().strip() or None
        vehicle.drive_type = self._drive_type.currentText()
        vehicle.fuel_type = self._fuel_type.currentText()
        vehicle.license_plate = self._license_plate.text().strip() or None
        vehicle.license_plate_state = self._license_plate_state.text().strip() or None
        vehicle.color = self._color.text().strip() or None
        vehicle.notes = self._notes.toPlainText().strip() or None
        if self.viewmodel.is_new:
            self.viewmodel.set_initial_mileage(self._mileage_input.value() or None)

    def _on_save_clicked(self) -> None:
        self._collect_form_into_viewmodel()
        self.viewmodel.save()

    def _on_saved(self, vehicle_id: int) -> None:
        if self._mileage_button.text() == "(set on save)":
            self._mileage_button.setText("Record Reading")
        self._mileage_input.setEnabled(True)
        self._mileage_button.setEnabled(True)
        self.saved.emit(vehicle_id)

    def _on_record_mileage(self) -> None:
        self.viewmodel.add_mileage_reading(self._mileage_input.value())

    def _on_error(self, message: str) -> None:
        QMessageBox.warning(self, "Error", message)
