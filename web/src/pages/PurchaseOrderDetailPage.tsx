import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ErrorBanner from "../components/ErrorBanner";
import StatusBadge from "../components/StatusBadge";
import { partsApi, purchaseOrdersApi, suppliersApi } from "../api/resources";
import type { Part, PurchaseOrder, Supplier } from "../api/types";

export default function PurchaseOrderDetailPage() {
  const { id } = useParams();
  const poId = Number(id);

  const [po, setPo] = useState<PurchaseOrder | null>(null);
  const [supplier, setSupplier] = useState<Supplier | null>(null);
  const [partsById, setPartsById] = useState<Record<number, Part>>({});
  const [error, setError] = useState<string | null>(null);
  const [receiveQty, setReceiveQty] = useState<Record<number, string>>({});
  const [returnPartId, setReturnPartId] = useState("");
  const [returnQty, setReturnQty] = useState("");

  const load = () => {
    purchaseOrdersApi
      .get(poId)
      .then((p) => {
        setPo(p);
        suppliersApi.get(p.supplier_id).then(setSupplier).catch((err) => setError(err.message));
        Promise.all(p.items.map((it) => partsApi.get(it.part_id)))
          .then((parts) => setPartsById(Object.fromEntries(parts.map((pt) => [pt.id, pt]))))
          .catch((err) => setError(err.message));
      })
      .catch((err) => setError(err.message));
  };

  useEffect(load, [poId]);

  if (!po) {
    return (
      <div>
        <ErrorBanner message={error} />
        {!error && <p className="muted">Loading…</p>}
      </div>
    );
  }

  const markOrdered = async () => {
    try {
      setPo(await purchaseOrdersApi.markOrdered(poId));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const cancel = async () => {
    if (!confirm("Cancel this purchase order?")) return;
    try {
      setPo(await purchaseOrdersApi.cancel(poId));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const submitReceive = async (e: React.FormEvent) => {
    e.preventDefault();
    const receipts = po.items
      .map((it) => ({ purchase_order_item_id: it.id, quantity: Number(receiveQty[it.id] || 0) }))
      .filter((r) => r.quantity > 0);
    if (receipts.length === 0) return;
    try {
      setPo(await purchaseOrdersApi.receive(poId, receipts));
      setReceiveQty({});
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const submitReturn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!returnPartId || !returnQty) return;
    try {
      await purchaseOrdersApi.recordReturn(poId, Number(returnPartId), Number(returnQty));
      setReturnPartId("");
      setReturnQty("");
      load();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const canReceive = po.status === "ordered" || po.status === "partially_received";
  const canCancel = po.status !== "cancelled" && po.status !== "received";

  return (
    <div>
      <div className="breadcrumb">
        <Link to="/purchase-orders">Purchase Orders</Link> / {po.purchase_order_number}
      </div>
      <div className="page-header">
        <h1>
          {po.purchase_order_number} <StatusBadge status={po.status} />
        </h1>
        <div style={{ display: "flex", gap: 10 }}>
          {po.status === "draft" && (
            <button className="primary" onClick={markOrdered}>
              Mark Ordered
            </button>
          )}
          {canCancel && (
            <button className="danger" onClick={cancel}>
              Cancel
            </button>
          )}
        </div>
      </div>
      <ErrorBanner message={error} />

      <div className="card">
        <h2>Details</h2>
        <p>
          Supplier:{" "}
          {supplier ? <Link to={`/suppliers/${supplier.id}`}>{supplier.name}</Link> : "—"}
        </p>
        <p>Tracking Number: {po.tracking_number || "—"}</p>
        <p>Notes: {po.notes || "—"}</p>
      </div>

      <div className="card">
        <h2>Items</h2>
        <table>
          <thead>
            <tr>
              <th>Part</th>
              <th>Ordered</th>
              <th>Received</th>
              <th>Unit Cost</th>
              {canReceive && <th>Receive Now</th>}
            </tr>
          </thead>
          <tbody>
            {po.items.map((item) => (
              <tr key={item.id}>
                <td>
                  {partsById[item.part_id] ? (
                    <Link to={`/parts/${item.part_id}`}>{partsById[item.part_id].part_number}</Link>
                  ) : (
                    `Part #${item.part_id}`
                  )}
                </td>
                <td>{item.quantity_ordered}</td>
                <td>{item.quantity_received}</td>
                <td>${item.unit_cost.toFixed(2)}</td>
                {canReceive && (
                  <td>
                    <input
                      type="number"
                      min={0}
                      max={item.quantity_ordered - item.quantity_received}
                      value={receiveQty[item.id] || ""}
                      onChange={(e) => setReceiveQty((prev) => ({ ...prev, [item.id]: e.target.value }))}
                      style={{ width: 70 }}
                      disabled={item.quantity_received >= item.quantity_ordered}
                    />
                  </td>
                )}
              </tr>
            ))}
            {po.items.length === 0 && (
              <tr>
                <td colSpan={canReceive ? 5 : 4} className="muted">
                  No items on this purchase order.
                </td>
              </tr>
            )}
          </tbody>
        </table>
        {canReceive && po.items.length > 0 && (
          <form onSubmit={submitReceive} style={{ marginTop: 12 }}>
            <button className="primary" type="submit">
              Record Receipt
            </button>
          </form>
        )}
      </div>

      {po.items.length > 0 && (
        <div className="card">
          <h2>Record Return To Supplier</h2>
          <form onSubmit={submitReturn} style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
            <div className="field" style={{ marginBottom: 0 }}>
              <label>Part</label>
              <select value={returnPartId} onChange={(e) => setReturnPartId(e.target.value)}>
                <option value="">Select…</option>
                {po.items.map((item) => (
                  <option key={item.part_id} value={item.part_id}>
                    {partsById[item.part_id]?.part_number || `Part #${item.part_id}`}
                  </option>
                ))}
              </select>
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label>Quantity</label>
              <input value={returnQty} onChange={(e) => setReturnQty(e.target.value)} style={{ width: 80 }} />
            </div>
            <button className="primary" type="submit">
              Record Return
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
