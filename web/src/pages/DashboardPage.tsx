import { useEffect, useState } from "react";
import ErrorBanner from "../components/ErrorBanner";
import { customersApi, invoicesApi, partsApi, repairOrdersApi, vehiclesApi } from "../api/resources";

interface Counts {
  customers: number;
  vehicles: number;
  openRepairOrders: number;
  unpaidInvoices: number;
  lowStockParts: number;
}

export default function DashboardPage() {
  const [counts, setCounts] = useState<Counts | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      customersApi.list(undefined, 1, 0),
      vehiclesApi.list(undefined, 1, 0),
      repairOrdersApi.list("in_progress", undefined, 1, 0),
      invoicesApi.list("partially_paid", undefined, 1, 0),
      partsApi.list(undefined, true, 1, 0),
    ])
      .then(([customers, vehicles, openRos, unpaidInvoices, lowStockParts]) => {
        setCounts({
          customers: customers.total,
          vehicles: vehicles.total,
          openRepairOrders: openRos.total,
          unpaidInvoices: unpaidInvoices.total,
          lowStockParts: lowStockParts.total,
        });
      })
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div>
      <h1>Dashboard</h1>
      <ErrorBanner message={error} />
      <div className="tiles">
        <div className="tile">
          <div className="value">{counts?.customers ?? "…"}</div>
          <div className="label">Total Customers</div>
        </div>
        <div className="tile">
          <div className="value">{counts?.vehicles ?? "…"}</div>
          <div className="label">Vehicles in System</div>
        </div>
        <div className="tile">
          <div className="value">{counts?.openRepairOrders ?? "…"}</div>
          <div className="label">Repair Orders In Progress</div>
        </div>
        <div className="tile">
          <div className="value">{counts?.unpaidInvoices ?? "…"}</div>
          <div className="label">Partially Paid Invoices</div>
        </div>
        <div className="tile">
          <div className="value">{counts?.lowStockParts ?? "…"}</div>
          <div className="label">Parts Below Minimum Stock</div>
        </div>
      </div>
    </div>
  );
}
