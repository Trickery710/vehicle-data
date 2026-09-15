import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import CustomerDetailPage from "./pages/CustomerDetailPage";
import CustomersPage from "./pages/CustomersPage";
import DashboardPage from "./pages/DashboardPage";
import DiagnosticSessionDetailPage from "./pages/DiagnosticSessionDetailPage";
import EstimateDetailPage from "./pages/EstimateDetailPage";
import InvoiceDetailPage from "./pages/InvoiceDetailPage";
import InvoicesPage from "./pages/InvoicesPage";
import PartDetailPage from "./pages/PartDetailPage";
import PartsPage from "./pages/PartsPage";
import PurchaseOrderDetailPage from "./pages/PurchaseOrderDetailPage";
import PurchaseOrderNewPage from "./pages/PurchaseOrderNewPage";
import PurchaseOrdersPage from "./pages/PurchaseOrdersPage";
import RepairOrderDetailPage from "./pages/RepairOrderDetailPage";
import RepairOrdersPage from "./pages/RepairOrdersPage";
import ReportsPage from "./pages/ReportsPage";
import SupplierDetailPage from "./pages/SupplierDetailPage";
import SuppliersPage from "./pages/SuppliersPage";
import VehicleDetailPage from "./pages/VehicleDetailPage";
import VehiclesPage from "./pages/VehiclesPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/customers" element={<CustomersPage />} />
        <Route path="/customers/:id" element={<CustomerDetailPage />} />
        <Route path="/vehicles" element={<VehiclesPage />} />
        <Route path="/vehicles/:id" element={<VehicleDetailPage />} />
        <Route path="/repair-orders" element={<RepairOrdersPage />} />
        <Route path="/repair-orders/:id" element={<RepairOrderDetailPage />} />
        <Route path="/invoices" element={<InvoicesPage />} />
        <Route path="/invoices/:id" element={<InvoiceDetailPage />} />
        <Route path="/estimates/:id" element={<EstimateDetailPage />} />
        <Route path="/parts" element={<PartsPage />} />
        <Route path="/parts/:id" element={<PartDetailPage />} />
        <Route path="/suppliers" element={<SuppliersPage />} />
        <Route path="/suppliers/:id" element={<SupplierDetailPage />} />
        <Route path="/purchase-orders" element={<PurchaseOrdersPage />} />
        <Route path="/purchase-orders/new" element={<PurchaseOrderNewPage />} />
        <Route path="/purchase-orders/:id" element={<PurchaseOrderDetailPage />} />
        <Route path="/diagnostic-sessions/:id" element={<DiagnosticSessionDetailPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
