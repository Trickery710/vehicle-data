import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ErrorBanner from "../components/ErrorBanner";
import StatusBadge from "../components/StatusBadge";
import { suppliersApi } from "../api/resources";
import type { PurchaseOrder, Supplier } from "../api/types";

export default function SupplierDetailPage() {
  const { id } = useParams();
  const supplierId = Number(id);
  const navigate = useNavigate();

  const [supplier, setSupplier] = useState<Supplier | null>(null);
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    suppliersApi.get(supplierId).then(setSupplier).catch((err) => setError(err.message));
    suppliersApi.purchaseOrders(supplierId).then(setPurchaseOrders).catch((err) => setError(err.message));
  };

  useEffect(load, [supplierId]);

  if (!supplier) {
    return (
      <div>
        <ErrorBanner message={error} />
        {!error && <p className="muted">Loading…</p>}
      </div>
    );
  }

  const update = async (field: keyof Supplier, value: string) => {
    try {
      setSupplier(await suppliersApi.update(supplierId, { [field]: value || null } as never));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const deactivate = async () => {
    if (!confirm("Deactivate this supplier?")) return;
    try {
      setSupplier(await suppliersApi.deactivate(supplierId));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div>
      <div className="breadcrumb">
        <Link to="/suppliers">Suppliers</Link> / {supplier.name}
      </div>
      <div className="page-header">
        <h1>{supplier.name}</h1>
        {supplier.is_active ? (
          <button className="danger" onClick={deactivate}>
            Deactivate
          </button>
        ) : (
          <span className="badge">Inactive</span>
        )}
      </div>
      <ErrorBanner message={error} />

      <div className="card">
        <h2>Details</h2>
        <div className="field-row">
          <div className="field">
            <label>Name</label>
            <input defaultValue={supplier.name} onBlur={(e) => update("name", e.target.value)} />
          </div>
          <div className="field">
            <label>Contact Name</label>
            <input
              defaultValue={supplier.contact_name || ""}
              onBlur={(e) => update("contact_name", e.target.value)}
            />
          </div>
          <div className="field">
            <label>Account Number</label>
            <input
              defaultValue={supplier.account_number || ""}
              onBlur={(e) => update("account_number", e.target.value)}
            />
          </div>
        </div>
        <div className="field-row">
          <div className="field">
            <label>Phone</label>
            <input defaultValue={supplier.phone || ""} onBlur={(e) => update("phone", e.target.value)} />
          </div>
          <div className="field">
            <label>Email</label>
            <input defaultValue={supplier.email || ""} onBlur={(e) => update("email", e.target.value)} />
          </div>
          <div className="field">
            <label>Website</label>
            <input defaultValue={supplier.website || ""} onBlur={(e) => update("website", e.target.value)} />
          </div>
        </div>
        <div className="field">
          <label>Notes</label>
          <textarea rows={3} defaultValue={supplier.notes || ""} onBlur={(e) => update("notes", e.target.value)} />
        </div>
      </div>

      <div className="card">
        <div className="section-title">
          <h2>Purchase Orders</h2>
          <button onClick={() => navigate(`/purchase-orders/new?supplier_id=${supplierId}`)}>
            New Purchase Order
          </button>
        </div>
        <table>
          <thead>
            <tr>
              <th>PO #</th>
              <th>Status</th>
              <th>Order Date</th>
            </tr>
          </thead>
          <tbody>
            {purchaseOrders.map((po) => (
              <tr key={po.id} className="clickable" onClick={() => navigate(`/purchase-orders/${po.id}`)}>
                <td>{po.purchase_order_number}</td>
                <td>
                  <StatusBadge status={po.status} />
                </td>
                <td>{po.order_date || "—"}</td>
              </tr>
            ))}
            {purchaseOrders.length === 0 && (
              <tr>
                <td colSpan={3} className="muted">
                  No purchase orders yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
