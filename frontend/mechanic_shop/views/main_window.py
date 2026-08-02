"""Main application window: navigation shell over Dashboard/Customers/Vehicles."""

from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.api_client.protocols import (
    CustomerApiClientProtocol,
    VehicleApiClientProtocol,
)
from frontend.mechanic_shop.theming.theme_manager import ThemeManager
from frontend.mechanic_shop.viewmodels.customer_detail_viewmodel import CustomerDetailViewModel
from frontend.mechanic_shop.viewmodels.customer_list_viewmodel import CustomerListViewModel
from frontend.mechanic_shop.viewmodels.dashboard_viewmodel import DashboardViewModel
from frontend.mechanic_shop.viewmodels.vehicle_detail_viewmodel import VehicleDetailViewModel
from frontend.mechanic_shop.viewmodels.vehicle_list_viewmodel import VehicleListViewModel
from frontend.mechanic_shop.views.customer_detail_view import CustomerDetailView
from frontend.mechanic_shop.views.customer_list_view import CustomerListView
from frontend.mechanic_shop.views.dashboard_view import DashboardView
from frontend.mechanic_shop.views.vehicle_detail_view import VehicleDetailView
from frontend.mechanic_shop.views.vehicle_list_view import VehicleListView
from shared.mechanic_shop_shared.constants import APP_NAME

_NAV_LABELS = ["Dashboard", "Customers", "Vehicles"]
_PAGE_DASHBOARD, _PAGE_CUSTOMERS, _PAGE_VEHICLES, _PAGE_DETAIL = range(4)


class MainWindow(QMainWindow):
    def __init__(
        self,
        customer_client: CustomerApiClientProtocol,
        vehicle_client: VehicleApiClientProtocol,
        theme_manager: ThemeManager,
    ) -> None:
        super().__init__()
        self._customer_client = customer_client
        self._vehicle_client = vehicle_client
        self._theme_manager = theme_manager

        self.setWindowTitle(APP_NAME)
        self.resize(1150, 750)

        self._nav_list = QListWidget()
        self._nav_list.setObjectName("navList")
        self._nav_list.setFixedWidth(180)
        self._nav_list.addItems(_NAV_LABELS)
        self._nav_list.currentRowChanged.connect(self._on_nav_changed)

        self._stack = QStackedWidget()

        self.dashboard_view = DashboardView(DashboardViewModel(customer_client, vehicle_client))
        self._stack.addWidget(self.dashboard_view)

        self.customer_list_view = CustomerListView(CustomerListViewModel(customer_client))
        self.customer_list_view.customer_selected.connect(self._open_customer_detail)
        self.customer_list_view.add_customer_requested.connect(
            lambda: self._open_customer_detail(None)
        )
        self._stack.addWidget(self.customer_list_view)

        self.vehicle_list_view = VehicleListView(VehicleListViewModel(vehicle_client))
        self.vehicle_list_view.vehicle_selected.connect(self._open_vehicle_detail)
        self._stack.addWidget(self.vehicle_list_view)

        self._detail_container = QWidget()
        self._detail_layout = QVBoxLayout(self._detail_container)
        self._detail_layout.setContentsMargins(0, 0, 0, 0)
        self._stack.addWidget(self._detail_container)

        central = QWidget()
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self._nav_list)
        central_layout.addWidget(self._stack, 1)
        self.setCentralWidget(central)

        self._build_menu()
        self.statusBar().showMessage("Ready")

        self._nav_list.setCurrentRow(_PAGE_DASHBOARD)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = self.menuBar().addMenu("&View")
        toggle_theme_action = QAction("Toggle &Theme", self)
        toggle_theme_action.triggered.connect(self._theme_manager.toggle)
        view_menu.addAction(toggle_theme_action)

        help_menu = self.menuBar().addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _show_about(self) -> None:
        body = (
            f"{APP_NAME}\nVersion 0.1.0\n\n"
            "Offline-first shop management for a one-person repair shop."
        )
        QMessageBox.information(self, f"About {APP_NAME}", body)

    def _on_nav_changed(self, row: int) -> None:
        if row == _PAGE_DASHBOARD:
            self._stack.setCurrentIndex(_PAGE_DASHBOARD)
            self.dashboard_view.refresh()
        elif row == _PAGE_CUSTOMERS:
            self._stack.setCurrentIndex(_PAGE_CUSTOMERS)
            self.customer_list_view.load()
        elif row == _PAGE_VEHICLES:
            self._stack.setCurrentIndex(_PAGE_VEHICLES)
            self.vehicle_list_view.load()

    def _clear_detail_container(self) -> None:
        while self._detail_layout.count():
            item = self._detail_layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _open_customer_detail(self, customer_id: int | None) -> None:
        self._clear_detail_container()
        viewmodel = CustomerDetailViewModel(self._customer_client, customer_id)
        view = CustomerDetailView(viewmodel)
        view.closed.connect(self._back_to_customers)
        view.saved.connect(lambda _cid: self._back_to_customers())
        view.vehicle_selected.connect(self._open_vehicle_detail)
        view.add_vehicle_requested.connect(self._open_new_vehicle_for_customer)
        self._detail_layout.addWidget(view)
        self._nav_list.setCurrentRow(-1)
        self._stack.setCurrentIndex(_PAGE_DETAIL)
        view.load()

    def _open_vehicle_detail(self, vehicle_id: int) -> None:
        # customer_id is a throwaway placeholder here: opening an existing
        # vehicle immediately fetches and replaces the whole Vehicle object
        # (with its real customer_id) via VehicleDetailViewModel.load().
        self._open_vehicle_detail_view(customer_id=0, vehicle_id=vehicle_id)

    def _open_new_vehicle_for_customer(self, customer_id: int) -> None:
        self._open_vehicle_detail_view(customer_id=customer_id, vehicle_id=None)

    def _open_vehicle_detail_view(self, customer_id: int, vehicle_id: int | None) -> None:
        self._clear_detail_container()
        viewmodel = VehicleDetailViewModel(self._vehicle_client, customer_id, vehicle_id)
        view = VehicleDetailView(viewmodel)
        view.closed.connect(self._back_to_vehicles)
        view.saved.connect(lambda _vid: self._back_to_vehicles())
        self._detail_layout.addWidget(view)
        self._nav_list.setCurrentRow(-1)
        self._stack.setCurrentIndex(_PAGE_DETAIL)
        view.load()

    def _back_to_customers(self) -> None:
        self._clear_detail_container()
        self._nav_list.setCurrentRow(_PAGE_CUSTOMERS)

    def _back_to_vehicles(self) -> None:
        self._clear_detail_container()
        self._nav_list.setCurrentRow(_PAGE_VEHICLES)
