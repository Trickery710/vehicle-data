"""Customer detail view: create/edit a customer, their phones, and their vehicles."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.api_client.protocols import ReportApiClientProtocol
from frontend.mechanic_shop.viewmodels.customer_detail_viewmodel import CustomerDetailViewModel
from frontend.mechanic_shop.views.widgets.phone_number_editor import PhoneNumberEditor
from shared.mechanic_shop_shared.enums import ContactMethod


class CustomerDetailView(QWidget):
    closed = Signal()
    saved = Signal(int)
    vehicle_selected = Signal(int)
    add_vehicle_requested = Signal(int)

    def __init__(
        self, viewmodel: CustomerDetailViewModel, report_client: ReportApiClientProtocol
    ) -> None:
        super().__init__()
        self.viewmodel = viewmodel
        self._report_client = report_client

        layout = QVBoxLayout(self)

        header_row = QHBoxLayout()
        back_button = QPushButton("< Back to Customers")
        back_button.clicked.connect(self.closed.emit)
        header_row.addWidget(back_button)
        header_row.addStretch(1)
        layout.addLayout(header_row)

        heading_text = "New Customer" if viewmodel.is_new else "Edit Customer"
        self._heading = QLabel(heading_text)
        self._heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(self._heading)

        form = QFormLayout()
        self._first_name = QLineEdit()
        self._last_name = QLineEdit()
        self._business_name = QLineEdit()
        self._email = QLineEdit()
        self._contact_method = QComboBox()
        self._contact_method.addItems([m.value for m in ContactMethod])
        self._address_line1 = QLineEdit()
        self._address_line2 = QLineEdit()
        self._city = QLineEdit()
        self._state = QLineEdit()
        self._state.setMaxLength(2)
        self._postal_code = QLineEdit()
        self._notes = QTextEdit()
        self._notes.setFixedHeight(80)

        form.addRow("First Name", self._first_name)
        form.addRow("Last Name", self._last_name)
        form.addRow("Business Name", self._business_name)
        form.addRow("Email", self._email)
        form.addRow("Preferred Contact", self._contact_method)
        form.addRow("Address Line 1", self._address_line1)
        form.addRow("Address Line 2", self._address_line2)
        form.addRow("City", self._city)
        form.addRow("State", self._state)
        form.addRow("Postal Code", self._postal_code)
        form.addRow("Notes", self._notes)
        layout.addLayout(form)

        layout.addWidget(QLabel("Phone Numbers"))
        self._phone_editor = PhoneNumberEditor()
        layout.addWidget(self._phone_editor)

        layout.addWidget(QLabel("Vehicles"))
        vehicles_row = QHBoxLayout()
        self._vehicles_list = QListWidget()
        self._vehicles_list.itemDoubleClicked.connect(self._on_vehicle_double_clicked)
        vehicles_row.addWidget(self._vehicles_list)
        layout.addLayout(vehicles_row)

        add_vehicle_button = QPushButton("Add Vehicle")
        add_vehicle_button.setEnabled(not viewmodel.is_new)
        add_vehicle_button.clicked.connect(
            lambda: self.add_vehicle_requested.emit(self.viewmodel.customer_id)
        )
        layout.addWidget(add_vehicle_button)
        self._add_vehicle_button = add_vehicle_button

        export_row = QHBoxLayout()
        export_row.addStretch(1)
        export_button = QPushButton("Export History Report...")
        export_button.setEnabled(not viewmodel.is_new)
        export_button.clicked.connect(self._on_export_history_clicked)
        self._export_button = export_button
        export_row.addWidget(export_button)
        layout.addLayout(export_row)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self._save_button = QPushButton("Save Customer")
        self._save_button.setObjectName("primaryButton")
        self._save_button.clicked.connect(self._on_save_clicked)
        button_row.addWidget(self._save_button)
        layout.addLayout(button_row)

        self.viewmodel.customer_loaded.connect(self._on_customer_loaded)
        self.viewmodel.vehicles_loaded.connect(self._on_vehicles_loaded)
        self.viewmodel.saved.connect(self._on_saved)
        self.viewmodel.error_occurred.connect(self._on_error)
        self.viewmodel.busy_changed.connect(self._save_button.setDisabled)

    def load(self) -> None:
        self.viewmodel.load()

    def _on_customer_loaded(self) -> None:
        customer = self.viewmodel.customer
        self._first_name.setText(customer.first_name or "")
        self._last_name.setText(customer.last_name or "")
        self._business_name.setText(customer.business_name or "")
        self._email.setText(customer.email or "")
        self._contact_method.setCurrentText(customer.preferred_contact_method)
        self._address_line1.setText(customer.address_line1 or "")
        self._address_line2.setText(customer.address_line2 or "")
        self._city.setText(customer.city or "")
        self._state.setText(customer.state or "")
        self._postal_code.setText(customer.postal_code or "")
        self._notes.setPlainText(customer.notes or "")
        self._phone_editor.set_phone_numbers(customer.phone_numbers)

    def _on_vehicles_loaded(self) -> None:
        self._vehicles_list.clear()
        for vehicle in self.viewmodel.vehicles:
            item = QListWidgetItem(vehicle.display_name)
            item.setData(1000, vehicle.id)
            self._vehicles_list.addItem(item)

    def _on_vehicle_double_clicked(self, item: QListWidgetItem) -> None:
        vehicle_id = item.data(1000)
        if vehicle_id is not None:
            self.vehicle_selected.emit(vehicle_id)

    def _collect_form_into_viewmodel(self) -> None:
        customer = self.viewmodel.customer
        customer.first_name = self._first_name.text().strip() or None
        customer.last_name = self._last_name.text().strip() or None
        customer.business_name = self._business_name.text().strip() or None
        customer.email = self._email.text().strip() or None
        customer.preferred_contact_method = self._contact_method.currentText()
        customer.address_line1 = self._address_line1.text().strip() or None
        customer.address_line2 = self._address_line2.text().strip() or None
        customer.city = self._city.text().strip() or None
        customer.state = self._state.text().strip() or None
        customer.postal_code = self._postal_code.text().strip() or None
        customer.notes = self._notes.toPlainText().strip() or None
        customer.phone_numbers = self._phone_editor.get_phone_numbers()

    def _on_save_clicked(self) -> None:
        self._collect_form_into_viewmodel()
        self.viewmodel.save()

    def _on_saved(self, customer_id: int) -> None:
        self._add_vehicle_button.setEnabled(True)
        self._export_button.setEnabled(True)
        self.saved.emit(customer_id)

    def _on_export_history_clicked(self) -> None:
        customer_id = self.viewmodel.customer_id
        if customer_id is None:
            return
        file_path, _filter = QFileDialog.getSaveFileName(
            self, "Export Customer History", f"customer_{customer_id}_history.pdf"
        )
        if not file_path:
            return
        fmt = "csv" if file_path.lower().endswith(".csv") else "pdf"

        def _do() -> bytes:
            content, _content_type = self._report_client.export_report(
                f"customer-history/{customer_id}", fmt
            )
            return content

        def _on_success(content: bytes) -> None:
            with open(file_path, "wb") as f:
                f.write(content)
            QMessageBox.information(self, "Export Complete", f"Report saved to:\n{file_path}")

        self.viewmodel.run_in_background(_do, on_success=_on_success)

    def _on_error(self, message: str) -> None:
        QMessageBox.warning(self, "Error", message)
