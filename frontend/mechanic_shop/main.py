"""Desktop application entrypoint.

Wires together: the local backend (spawned or connected-to via
``ServerManager``), the HTTP API clients, the theme manager, and the main
window. On exit, the backend subprocess (if this process spawned one) is
terminated.
"""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from frontend.mechanic_shop.api_client.attachment_client import AttachmentApiClient
from frontend.mechanic_shop.api_client.base_client import ApiClient
from frontend.mechanic_shop.api_client.customer_client import CustomerApiClient
from frontend.mechanic_shop.api_client.diagnostic_client import DiagnosticApiClient
from frontend.mechanic_shop.api_client.estimate_client import EstimateApiClient
from frontend.mechanic_shop.api_client.invoice_client import InvoiceApiClient
from frontend.mechanic_shop.api_client.part_client import PartApiClient
from frontend.mechanic_shop.api_client.purchase_order_client import PurchaseOrderApiClient
from frontend.mechanic_shop.api_client.repair_order_client import RepairOrderApiClient
from frontend.mechanic_shop.api_client.report_client import ReportApiClient
from frontend.mechanic_shop.api_client.supplier_client import SupplierApiClient
from frontend.mechanic_shop.api_client.vehicle_client import VehicleApiClient
from frontend.mechanic_shop.logging_config import configure_logging
from frontend.mechanic_shop.server_manager import BackendStartupError, ServerManager
from frontend.mechanic_shop.theming.theme_manager import ThemeManager
from frontend.mechanic_shop.views.main_window import MainWindow
from shared.mechanic_shop_shared.constants import APP_NAME

logger = logging.getLogger(__name__)


def main() -> int:
    configure_logging()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    server_manager = ServerManager()
    try:
        server_manager.start()
    except BackendStartupError as exc:
        logger.exception("Backend failed to start")
        QMessageBox.critical(None, f"{APP_NAME} -- Startup Error", str(exc))
        return 1

    app.aboutToQuit.connect(server_manager.stop)

    api_client = ApiClient(base_url=server_manager.api_base_url)
    customer_client = CustomerApiClient(api_client)
    vehicle_client = VehicleApiClient(api_client)
    estimate_client = EstimateApiClient(api_client)
    repair_order_client = RepairOrderApiClient(api_client)
    invoice_client = InvoiceApiClient(api_client)
    attachment_client = AttachmentApiClient(api_client)
    part_client = PartApiClient(api_client)
    supplier_client = SupplierApiClient(api_client)
    purchase_order_client = PurchaseOrderApiClient(api_client)
    diagnostic_client = DiagnosticApiClient(api_client)
    report_client = ReportApiClient(api_client)

    theme_manager = ThemeManager(app)
    theme_manager.apply_saved_theme()

    window = MainWindow(
        customer_client,
        vehicle_client,
        estimate_client,
        repair_order_client,
        invoice_client,
        attachment_client,
        part_client,
        supplier_client,
        purchase_order_client,
        diagnostic_client,
        report_client,
        theme_manager,
    )
    window.show()

    exit_code = app.exec()
    api_client.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
