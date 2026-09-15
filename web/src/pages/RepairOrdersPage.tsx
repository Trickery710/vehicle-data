import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ErrorBanner from "../components/ErrorBanner";
import StatusBadge from "../components/StatusBadge";
import { repairOrdersApi } from "../api/resources";
import type { RepairOrder } from "../api/types";
import { REPAIR_ORDER_STATUSES } from "../api/types";

export default function RepairOrdersPage() {
  const [items, setItems] = useState<RepairOrder[]>([]);
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    repairOrdersApi
      .list(status || undefined, q || undefined)
      .then((res) => setItems(res.items))
      .catch((err) => setError(err.message));
  }, [status, q]);

  return (
    <div>
      <div className="page-header">
        <h1>Repair Orders</h1>
      </div>
      <ErrorBanner message={error} />
      <p className="muted">New repair orders are created from a vehicle's detail page.</p>

      <div className="toolbar">
        <input
          placeholder="Search RO number or complaint…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          style={{ minWidth: 260 }}
        />
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          {REPAIR_ORDER_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s.replace(/_/g, " ")}
            </option>
          ))}
        </select>
      </div>

      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>RO #</th>
              <th>Status</th>
              <th>Complaint</th>
              <th>Technician</th>
            </tr>
          </thead>
          <tbody>
            {items.map((ro) => (
              <tr key={ro.id} className="clickable" onClick={() => navigate(`/repair-orders/${ro.id}`)}>
                <td>{ro.repair_order_number}</td>
                <td>
                  <StatusBadge status={ro.status} />
                </td>
                <td>{ro.complaint || "—"}</td>
                <td>{ro.assigned_technician || "—"}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={4} className="muted">
                  No repair orders found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
