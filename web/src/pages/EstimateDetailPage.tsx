import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ErrorBanner from "../components/ErrorBanner";
import LineItemsEditor from "../components/LineItemsEditor";
import StatusBadge from "../components/StatusBadge";
import { estimatesApi } from "../api/resources";
import type { Estimate, LineItem, LineItemInput } from "../api/types";

export default function EstimateDetailPage() {
  const { id } = useParams();
  const estimateId = Number(id);
  const navigate = useNavigate();

  const [estimate, setEstimate] = useState<Estimate | null>(null);
  const [lineItems, setLineItems] = useState<LineItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [signerName, setSignerName] = useState("");

  const load = () => {
    estimatesApi.get(estimateId).then(setEstimate).catch((err) => setError(err.message));
    estimatesApi.lineItems(estimateId).then(setLineItems).catch((err) => setError(err.message));
  };

  useEffect(load, [estimateId]);

  if (!estimate) {
    return (
      <div>
        <ErrorBanner message={error} />
        {!error && <p className="muted">Loading…</p>}
      </div>
    );
  }

  const update = async (field: keyof Estimate, value: string) => {
    try {
      setEstimate(await estimatesApi.update(estimateId, { [field]: value || null } as never));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const saveLineItems = async (items: LineItemInput[]) => {
    try {
      setLineItems(await estimatesApi.replaceLineItems(estimateId, items));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const send = async () => {
    try {
      setEstimate(await estimatesApi.send(estimateId));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const approve = async () => {
    try {
      setEstimate(await estimatesApi.approve(estimateId, signerName || undefined));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const decline = async () => {
    try {
      setEstimate(await estimatesApi.decline(estimateId));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const deleteEstimate = async () => {
    if (!confirm("Delete this draft estimate?")) return;
    try {
      await estimatesApi.delete(estimateId);
      navigate(`/vehicles/${estimate.vehicle_id}`);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const convertToRepairOrder = async () => {
    try {
      const ro = await estimatesApi.convertToRepairOrder(estimateId);
      navigate(`/repair-orders/${ro.id}`);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const editable = estimate.status === "draft";

  return (
    <div>
      <div className="breadcrumb">
        <Link to={`/vehicles/${estimate.vehicle_id}`}>Vehicle</Link> / {estimate.estimate_number}
      </div>
      <div className="page-header">
        <h1>
          {estimate.estimate_number} <StatusBadge status={estimate.status} />
        </h1>
        <div style={{ display: "flex", gap: 10 }}>
          {estimate.status === "draft" && (
            <>
              <button className="primary" onClick={send}>
                Send
              </button>
              <button className="danger" onClick={deleteEstimate}>
                Delete
              </button>
            </>
          )}
          {estimate.status === "sent" && (
            <button className="danger" onClick={decline}>
              Decline
            </button>
          )}
        </div>
      </div>
      <ErrorBanner message={error} />

      <div className="card">
        <h2>Details</h2>
        <div className="field">
          <label>Title</label>
          <input defaultValue={estimate.title || ""} onBlur={(e) => update("title", e.target.value)} disabled={!editable} />
        </div>
        <div className="field">
          <label>Notes</label>
          <textarea
            rows={3}
            defaultValue={estimate.notes || ""}
            onBlur={(e) => update("notes", e.target.value)}
            disabled={!editable}
          />
        </div>
      </div>

      <div className="card">
        <h2>Line Items</h2>
        <LineItemsEditor items={lineItems} onSave={saveLineItems} readOnly={!editable} />
      </div>

      {estimate.status === "sent" && (
        <div className="card">
          <h2>Approve</h2>
          <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
            <div className="field" style={{ marginBottom: 0 }}>
              <label>Signer Name</label>
              <input value={signerName} onChange={(e) => setSignerName(e.target.value)} />
            </div>
            <button className="primary" onClick={approve}>
              Approve
            </button>
          </div>
        </div>
      )}

      {estimate.status === "approved" && (
        <div className="card">
          <h2>Convert to Repair Order</h2>
          <button className="primary" onClick={convertToRepairOrder}>
            Convert to Repair Order
          </button>
        </div>
      )}
    </div>
  );
}
