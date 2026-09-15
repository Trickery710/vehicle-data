import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ErrorBanner from "../components/ErrorBanner";
import StatusBadge from "../components/StatusBadge";
import { purchaseOrdersApi } from "../api/resources";
import type { PurchaseOrder } from "../api/types";
import { PURCHASE_ORDER_STATUSES } from "../api/types";

export default function PurchaseOrdersPage() {
  const [items, setItems] = useState<PurchaseOrder[]>([]);
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    purchaseOrdersApi
      .list(status || undefined, q || undefined)
      .then((res) => setItems(res.items))
      .catch((err) => setError(err.message));
  }, [status, q]);

  return (
    <div>
      <div className="page-header">
        <h1>Purchase Orders</h1>
        <button className="primary" onClick={() => navigate("/purchase-orders/new")}>
          New Purchase Order
        </button>
      </div>
      <ErrorBanner message={error} />

      <div className="toolbar">
        <input
          placeholder="Search PO number…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          style={{ minWidth: 260 }}
        />
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          {PURCHASE_ORDER_STATUSES.map((s) => (
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
              <th>PO #</th>
              <th>Status</th>
              <th>Order Date</th>
              <th>Expected Delivery</th>
            </tr>
          </thead>
          <tbody>
            {items.map((po) => (
              <tr key={po.id} className="clickable" onClick={() => navigate(`/purchase-orders/${po.id}`)}>
                <td>{po.purchase_order_number}</td>
                <td>
                  <StatusBadge status={po.status} />
                </td>
                <td>{po.order_date || "—"}</td>
                <td>{po.expected_delivery_date || "—"}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={4} className="muted">
                  No purchase orders found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
