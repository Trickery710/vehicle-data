import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ErrorBanner from "../components/ErrorBanner";
import StatusBadge from "../components/StatusBadge";
import { apiUrl } from "../api/client";
import { diagnosticsApi, estimatesApi, repairOrdersApi, vehiclesApi } from "../api/resources";
import type { DiagnosticSession, Estimate, Invoice, RepairOrder, TimelineEvent, Vehicle } from "../api/types";
import { DRIVE_TYPES, FUEL_TYPES } from "../api/types";

export default function VehicleDetailPage() {
  const { id } = useParams();
  const vehicleId = Number(id);
  const navigate = useNavigate();

  const [vehicle, setVehicle] = useState<Vehicle | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [repairOrders, setRepairOrders] = useState<RepairOrder[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [estimates, setEstimates] = useState<Estimate[]>([]);
  const [diagnosticSessions, setDiagnosticSessions] = useState<DiagnosticSession[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [mileageInput, setMileageInput] = useState("");
  const [creatingRo, setCreatingRo] = useState(false);
  const [complaint, setComplaint] = useState("");
  const [creatingEstimate, setCreatingEstimate] = useState(false);
  const [estimateTitle, setEstimateTitle] = useState("");

  const load = () => {
    vehiclesApi.get(vehicleId).then(setVehicle).catch((err) => setError(err.message));
    vehiclesApi.timeline(vehicleId).then(setTimeline).catch((err) => setError(err.message));
    vehiclesApi.repairOrders(vehicleId).then(setRepairOrders).catch((err) => setError(err.message));
    vehiclesApi.invoices(vehicleId).then(setInvoices).catch((err) => setError(err.message));
    vehiclesApi.estimates(vehicleId).then(setEstimates).catch((err) => setError(err.message));
    vehiclesApi
      .diagnosticSessions(vehicleId)
      .then(setDiagnosticSessions)
      .catch((err) => setError(err.message));
  };

  useEffect(load, [vehicleId]);

  if (!vehicle) {
    return (
      <div>
        <ErrorBanner message={error} />
        {!error && <p className="muted">Loading…</p>}
      </div>
    );
  }

  const update = async (field: keyof Vehicle, value: string) => {
    try {
      const updated = await vehiclesApi.update(vehicleId, { [field]: value || null } as never);
      setVehicle(updated);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const deactivate = async () => {
    if (!confirm("Deactivate this vehicle?")) return;
    try {
      setVehicle(await vehiclesApi.deactivate(vehicleId));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const submitMileage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mileageInput) return;
    try {
      const updated = await vehiclesApi.addMileage(vehicleId, Number(mileageInput));
      setVehicle(updated);
      setMileageInput("");
      vehiclesApi.timeline(vehicleId).then(setTimeline);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const createRepairOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const ro = await repairOrdersApi.create({ vehicle_id: vehicleId, complaint: complaint || null });
      navigate(`/repair-orders/${ro.id}`);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const createEstimate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const est = await estimatesApi.create({ vehicle_id: vehicleId, title: estimateTitle || null });
      navigate(`/estimates/${est.id}`);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const name = [vehicle.year, vehicle.make, vehicle.model].filter(Boolean).join(" ") || `Vehicle #${vehicle.id}`;

  return (
    <div>
      <div className="breadcrumb">
        <Link to="/vehicles">Vehicles</Link> / {name}
      </div>
      <div className="page-header">
        <h1>{name}</h1>
        <div style={{ display: "flex", gap: 10 }}>
          <a
            className="link-button"
            href={apiUrl(`/reports/vehicle-history/${vehicleId}?format=pdf`)}
            target="_blank"
            rel="noreferrer"
          >
            <button type="button">Export History Report</button>
          </a>
          {vehicle.is_active ? (
            <button className="danger" onClick={deactivate}>
              Deactivate
            </button>
          ) : (
            <span className="badge">Inactive</span>
          )}
        </div>
      </div>
      <ErrorBanner message={error} />

      <div className="card">
        <h2>Details</h2>
        <div className="field-row">
          <div className="field">
            <label>VIN</label>
            <input defaultValue={vehicle.vin || ""} onBlur={(e) => update("vin", e.target.value)} maxLength={17} />
          </div>
          <div className="field">
            <label>Year</label>
            <input defaultValue={vehicle.year ?? ""} onBlur={(e) => update("year", e.target.value)} />
          </div>
          <div className="field">
            <label>Make</label>
            <input defaultValue={vehicle.make || ""} onBlur={(e) => update("make", e.target.value)} />
          </div>
          <div className="field">
            <label>Model</label>
            <input defaultValue={vehicle.model || ""} onBlur={(e) => update("model", e.target.value)} />
          </div>
        </div>
        <div className="field-row">
          <div className="field">
            <label>License Plate</label>
            <input
              defaultValue={vehicle.license_plate || ""}
              onBlur={(e) => update("license_plate", e.target.value)}
            />
          </div>
          <div className="field">
            <label>Color</label>
            <input defaultValue={vehicle.color || ""} onBlur={(e) => update("color", e.target.value)} />
          </div>
          <div className="field">
            <label>Drive Type</label>
            <select defaultValue={vehicle.drive_type} onChange={(e) => update("drive_type", e.target.value)}>
              {DRIVE_TYPES.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Fuel Type</label>
            <select defaultValue={vehicle.fuel_type} onChange={(e) => update("fuel_type", e.target.value)}>
              {FUEL_TYPES.map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="card">
        <h2>Mileage</h2>
        <p>
          Current: <strong>{vehicle.current_mileage ?? "unknown"}</strong>
        </p>
        <form onSubmit={submitMileage} style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
          <div className="field" style={{ marginBottom: 0 }}>
            <label>New Reading</label>
            <input value={mileageInput} onChange={(e) => setMileageInput(e.target.value)} />
          </div>
          <button className="primary" type="submit">
            Record
          </button>
        </form>
      </div>

      <div className="card">
        <div className="section-title">
          <h2>Estimates</h2>
          <button onClick={() => setCreatingEstimate((v) => !v)}>
            {creatingEstimate ? "Cancel" : "New Estimate"}
          </button>
        </div>
        {creatingEstimate && (
          <form onSubmit={createEstimate} style={{ marginBottom: 16 }}>
            <div className="field">
              <label>Title</label>
              <input value={estimateTitle} onChange={(e) => setEstimateTitle(e.target.value)} />
            </div>
            <button className="primary" type="submit">
              Create
            </button>
          </form>
        )}
        <table>
          <thead>
            <tr>
              <th>Estimate #</th>
              <th>Status</th>
              <th>Title</th>
            </tr>
          </thead>
          <tbody>
            {estimates.map((est) => (
              <tr key={est.id} className="clickable" onClick={() => navigate(`/estimates/${est.id}`)}>
                <td>{est.estimate_number}</td>
                <td>
                  <StatusBadge status={est.status} />
                </td>
                <td>{est.title || "—"}</td>
              </tr>
            ))}
            {estimates.length === 0 && (
              <tr>
                <td colSpan={3} className="muted">
                  No estimates yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="card">
        <div className="section-title">
          <h2>Repair Orders</h2>
          <button onClick={() => setCreatingRo((v) => !v)}>{creatingRo ? "Cancel" : "New Repair Order"}</button>
        </div>
        {creatingRo && (
          <form onSubmit={createRepairOrder} style={{ marginBottom: 16 }}>
            <div className="field">
              <label>Complaint</label>
              <textarea rows={2} value={complaint} onChange={(e) => setComplaint(e.target.value)} />
            </div>
            <button className="primary" type="submit">
              Create
            </button>
          </form>
        )}
        <table>
          <thead>
            <tr>
              <th>RO #</th>
              <th>Status</th>
              <th>Complaint</th>
            </tr>
          </thead>
          <tbody>
            {repairOrders.map((ro) => (
              <tr key={ro.id} className="clickable" onClick={() => navigate(`/repair-orders/${ro.id}`)}>
                <td>{ro.repair_order_number}</td>
                <td>
                  <StatusBadge status={ro.status} />
                </td>
                <td>{ro.complaint || "—"}</td>
              </tr>
            ))}
            {repairOrders.length === 0 && (
              <tr>
                <td colSpan={3} className="muted">
                  No repair orders yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2>Invoices</h2>
        <table>
          <thead>
            <tr>
              <th>Invoice #</th>
              <th>Status</th>
              <th>Due Date</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map((inv) => (
              <tr key={inv.id} className="clickable" onClick={() => navigate(`/invoices/${inv.id}`)}>
                <td>{inv.invoice_number}</td>
                <td>
                  <StatusBadge status={inv.status} />
                </td>
                <td>{inv.due_date || "—"}</td>
              </tr>
            ))}
            {invoices.length === 0 && (
              <tr>
                <td colSpan={3} className="muted">
                  No invoices yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="card">
        <div className="section-title">
          <h2>Diagnostic Sessions</h2>
          <button
            onClick={async () => {
              try {
                const session = await diagnosticsApi.create({ vehicle_id: vehicleId });
                navigate(`/diagnostic-sessions/${session.id}`);
              } catch (err) {
                setError((err as Error).message);
              }
            }}
          >
            New Diagnostic Session
          </button>
        </div>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Summary</th>
              <th>Trouble Codes</th>
            </tr>
          </thead>
          <tbody>
            {diagnosticSessions.map((s) => (
              <tr key={s.id} className="clickable" onClick={() => navigate(`/diagnostic-sessions/${s.id}`)}>
                <td>{new Date(s.session_date).toLocaleDateString()}</td>
                <td>{s.summary || "—"}</td>
                <td>{s.trouble_codes.length}</td>
              </tr>
            ))}
            {diagnosticSessions.length === 0 && (
              <tr>
                <td colSpan={3} className="muted">
                  No diagnostic sessions yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2>Timeline</h2>
        <ul>
          {timeline.map((ev) => (
            <li key={ev.id}>
              <span className="muted">{new Date(ev.event_timestamp).toLocaleString()}</span> — {ev.title}
            </li>
          ))}
          {timeline.length === 0 && <li className="muted">No history yet.</li>}
        </ul>
      </div>
    </div>
  );
}
