"""Editable list of a customer's phone numbers (add/remove, one primary)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.models.customer import PhoneNumber
from shared.mechanic_shop_shared.enums import PhoneType

_COLUMNS = ["Phone Number", "Type", "Primary", ""]


class PhoneNumberEditor(QWidget):
    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget(0, len(_COLUMNS))
        self._table.setHorizontalHeaderLabels(_COLUMNS)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

        add_row = QHBoxLayout()
        self._number_input = QLineEdit()
        self._number_input.setPlaceholderText("Phone number")
        self._type_combo = QComboBox()
        self._type_combo.addItems([t.value for t in PhoneType])
        add_button = QPushButton("Add")
        add_button.clicked.connect(self._on_add_clicked)
        add_row.addWidget(self._number_input, stretch=1)
        add_row.addWidget(self._type_combo)
        add_row.addWidget(add_button)
        layout.addLayout(add_row)

    def set_phone_numbers(self, phones: list[PhoneNumber]) -> None:
        self._table.setRowCount(0)
        for phone in phones:
            self._add_row(phone)

    def get_phone_numbers(self) -> list[PhoneNumber]:
        phones = []
        for row in range(self._table.rowCount()):
            number_item = self._table.item(row, 0)
            type_item = self._table.item(row, 1)
            if number_item is None or type_item is None:
                continue  # rows are always populated by _add_row; defensive only
            number = number_item.text().strip()
            if not number:
                continue
            phone_type = type_item.text()
            checkbox = self._table.cellWidget(row, 2)
            is_primary = checkbox.isChecked() if isinstance(checkbox, QCheckBox) else False
            phones.append(
                PhoneNumber(
                    id=None, phone_number=number, phone_type=phone_type, is_primary=is_primary
                )
            )
        return phones

    def _add_row(self, phone: PhoneNumber) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QTableWidgetItem(phone.phone_number))
        self._table.setItem(row, 1, QTableWidgetItem(phone.phone_type))

        checkbox = QCheckBox()
        checkbox.setChecked(phone.is_primary)
        checkbox.toggled.connect(self.changed.emit)
        self._table.setCellWidget(row, 2, checkbox)

        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(
            lambda _checked, b=remove_button: self._remove_row_by_widget(b)
        )
        self._table.setCellWidget(row, 3, remove_button)

    def _remove_row_by_widget(self, button: QPushButton) -> None:
        # Row indices shift as rows are removed, so the current row must be
        # found by widget identity at click time rather than captured once.
        for row in range(self._table.rowCount()):
            if self._table.cellWidget(row, 3) is button:
                self._table.removeRow(row)
                break
        self.changed.emit()

    def _on_add_clicked(self) -> None:
        number = self._number_input.text().strip()
        if not number:
            return
        phone = PhoneNumber(id=None, phone_number=number, phone_type=self._type_combo.currentText())
        self._add_row(phone)
        self._number_input.clear()
        self.changed.emit()
