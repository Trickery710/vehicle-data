import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ErrorBanner from "../components/ErrorBanner";
import LineItemsEditor from "../components/LineItemsEditor";
import StatusBadge from "../components/StatusBadge";
import { partsApi, repairOrdersApi } from "../api/resources";
import type { LineItem, LineItemInput, Part, RepairOrder } from "../api/types";
import { REPAIR_ORDER_STATUSES } from "../api/types";

export default function RepairOrderDetailPage() {
  const { id } = useParams();
  const repairOrderId = Number(id);
  const navigate = useNavigate();

  const [ro, setRo] = useState<RepairOrder | null>(null);
  const [lineItems, setLineItems] = useState<LineItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [taxRate, setTaxRate] = useState("0");
  const [parts, setParts] = useState<Part[]>([]);
  const [selectedPartId, setSelectedPartId] = useState("");
  const [partQuantity, setPartQuantity] = useState("1");

  const load = () => {
    repairOrdersApi.get(repairOrderId).then(setRo).catch((err) => setError(err.message));
    repairOrdersApi.lineItems(repairOrderId).then(setLineItems).catch((err) => setError(err.message));
    partsApi.list(undefined, false, 200).then((res) => setParts(res.items)).catch((err) => setError(err.message));
  };

  useEffect(load, [repairOrderId]);

  if (!ro) {
    return (
      <div>
        <ErrorBanner message={error} />
        {!error && <p className="muted">Loading…</p>}
      </div>
    );
  }

  const update = async (field: keyof RepairOrder, value: string) => {
    try {
      setRo(await repairOrdersApi.update(repairOrderId, { [field]: value || null } as never));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const changeStatus = async (status: string) => {
    try {
      setRo(await repairOrdersApi.updateStatus(repairOrderId, status));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const cancelRo = async () => {
    if (!confirm("Cancel this repair order?")) return;
    try {
      setRo(await repairOrdersApi.cancel(repairOrderId));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const saveLineItems = async (items: LineItemInput[]) => {
    try {
      setLineItems(await repairOrdersApi.replaceLineItems(repairOrderId, items));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const addPartFromInventory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPartId) return;
    try {
      await repairOrdersApi.addPartFromInventory(repairOrderId, Number(selectedPartId), Number(partQuantity) || 1);
      setSelectedPartId("");
      setPartQuantity("1");
      repairOrdersApi.lineItems(repairOrderId).then(setLineItems);
      partsApi.list(undefined, false, 200).then((res) => setParts(res.items));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const convertToInvoice = async () => {
    try {
      const invoice = await repairOrdersApi.convertToInvoice(repairOrderId, Number(taxRate) || 0);
      navigate(`/invoices/${invoice.id}`);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const canCancel = ro.status !== "cancelled" && ro.status !== "delivered";

  return (
    <div>
      <div className="breadcrumb">
        <Link to="/repair-orders">Repair Orders</Link> / {ro.repair_order_number}
      </div>
      <div className="page-header">
        <h1>
          {ro.repair_order_number} <StatusBadge status={ro.status} />
        </h1>
        {canCancel && (
          <button className="danger" onClick={cancelRo}>
            Cancel RO
          </button>
        )}
      </div>
      <ErrorBanner message={error} />

      <div className="card">
        <h2>Status</h2>
        <div className="field" style={{ maxWidth: 260 }}>
          <label>Change Status</label>
          <select value={ro.status} onChange={(e) => changeStatus(e.target.value)}>
            {REPAIR_ORDER_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="card">
        <h2>Job Details</h2>
        <div className="field-row">
          <div className="field">
            <label>Assigned Technician</label>
            <input
              defaultValue={ro.assigned_technician || ""}
              onBlur={(e) => update("assigned_technician", e.target.value)}
            />
          </div>
        </div>
        <div className="field">
          <label>Complaint</label>
          <textarea rows={2} defaultValue={ro.complaint || ""} onBlur={(e) => update("complaint", e.target.value)} />
        </div>
        <div className="field">
          <label>Cause</label>
          <textarea rows={2} defaultValue={ro.cause || ""} onBlur={(e) => update("cause", e.target.value)} />
        </div>
        <div className="field">
          <label>Correction</label>
          <textarea
            rows={2}
            defaultValue={ro.correction || ""}
            onBlur={(e) => update("correction", e.target.value)}
          />
        </div>
        <div className="field">
          <label>Technician Notes</label>
          <textarea
            rows={2}
            defaultValue={ro.technician_notes || ""}
            onBlur={(e) => update("technician_notes", e.target.value)}
          />
        </div>
      </div>

      <div className="card">
        <h2>Line Items</h2>
        <LineItemsEditor items={lineItems} onSave={saveLineItems} />
      </div>

      <div className="card">
        <h2>Add Part From Inventory</h2>
        <p className="muted">Atomically adds a part line item and decrements stock.</p>
        <form onSubmit={addPartFromInventory} style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
          <div className="field" style={{ marginBottom: 0, minWidth: 260 }}>
            <label>Part</label>
            <select value={selectedPartId} onChange={(e) => setSelectedPartId(e.target.value)}>
              <option value="">Select a part…</option>
              {parts.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.part_number} — {p.description} ({p.quantity_on_hand} in stock)
                </option>
              ))}
            </select>
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label>Quantity</label>
            <input value={partQuantity} onChange={(e) => setPartQuantity(e.target.value)} style={{ width: 80 }} />
          </div>
          <button className="primary" type="submit" disabled={!selectedPartId}>
            Add Part
          </button>
        </form>
      </div>

      <div className="card">
        <h2>Convert to Invoice</h2>
        <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
          <div className="field" style={{ marginBottom: 0 }}>
            <label>Tax Rate (%)</label>
            <input value={taxRate} onChange={(e) => setTaxRate(e.target.value)} style={{ width: 100 }} />
          </div>
          <button className="primary" onClick={convertToInvoice} disabled={ro.status === "cancelled"}>
            Convert to Invoice
          </button>
        </div>
      </div>
    </div>
  );
}
