import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ErrorBanner from "../components/ErrorBanner";
import { apiUrl } from "../api/client";
import { customersApi, vehiclesApi } from "../api/resources";
import type { Customer, Vehicle } from "../api/types";
import { CONTACT_METHODS } from "../api/types";

function vehicleName(v: Vehicle): string {
  return [v.year, v.make, v.model].filter(Boolean).join(" ") || `Vehicle #${v.id}`;
}

export default function CustomerDetailPage() {
  const { id } = useParams();
  const customerId = Number(id);
  const navigate = useNavigate();

  const [customer, setCustomer] = useState<Customer | null>(null);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [showAddVehicle, setShowAddVehicle] = useState(false);
  const [vin, setVin] = useState("");
  const [make, setMake] = useState("");
  const [model, setModel] = useState("");
  const [year, setYear] = useState("");

  const load = () => {
    customersApi.get(customerId).then(setCustomer).catch((err) => setError(err.message));
    customersApi.vehicles(customerId).then(setVehicles).catch((err) => setError(err.message));
  };

  useEffect(load, [customerId]);

  if (!customer) {
    return (
      <div>
        <ErrorBanner message={error} />
        {!error && <p className="muted">Loading…</p>}
      </div>
    );
  }

  const update = async (field: keyof Customer, value: string) => {
    setSaving(true);
    try {
      const updated = await customersApi.update(customerId, { [field]: value || null } as never);
      setCustomer(updated);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const deactivate = async () => {
    if (!confirm("Deactivate this customer?")) return;
    try {
      const updated = await customersApi.deactivate(customerId);
      setCustomer(updated);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const addVehicle = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await vehiclesApi.create({
        customer_id: customerId,
        vin: vin || null,
        make: make || null,
        model: model || null,
        year: year ? Number(year) : null,
      });
      setShowAddVehicle(false);
      setVin("");
      setMake("");
      setModel("");
      setYear("");
      navigate(`/vehicles/${created.id}`);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const name = customer.business_name || [customer.first_name, customer.last_name].filter(Boolean).join(" ");

  return (
    <div>
      <div className="breadcrumb">
        <Link to="/customers">Customers</Link> / {name}
      </div>
      <div className="page-header">
        <h1>{name || `Customer #${customer.id}`}</h1>
        <div style={{ display: "flex", gap: 10 }}>
          <a
            className="link-button"
            href={apiUrl(`/reports/customer-history/${customerId}?format=pdf`)}
            target="_blank"
            rel="noreferrer"
          >
            <button type="button">Export History Report</button>
          </a>
          {customer.is_active ? (
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
            <label>First Name</label>
            <input
              defaultValue={customer.first_name || ""}
              onBlur={(e) => update("first_name", e.target.value)}
            />
          </div>
          <div className="field">
            <label>Last Name</label>
            <input
              defaultValue={customer.last_name || ""}
              onBlur={(e) => update("last_name", e.target.value)}
            />
          </div>
          <div className="field">
            <label>Business Name</label>
            <input
              defaultValue={customer.business_name || ""}
              onBlur={(e) => update("business_name", e.target.value)}
            />
          </div>
        </div>
        <div className="field-row">
          <div className="field">
            <label>Email</label>
            <input defaultValue={customer.email || ""} onBlur={(e) => update("email", e.target.value)} />
          </div>
          <div className="field">
            <label>Preferred Contact</label>
            <select
              defaultValue={customer.preferred_contact_method}
              onChange={(e) => update("preferred_contact_method", e.target.value)}
            >
              {CONTACT_METHODS.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="field">
          <label>Notes</label>
          <textarea
            rows={3}
            defaultValue={customer.notes || ""}
            onBlur={(e) => update("notes", e.target.value)}
          />
        </div>
        {saving && <span className="muted">Saving…</span>}
      </div>

      <div className="card">
        <h2>Phone Numbers</h2>
        {customer.phone_numbers.length === 0 && <p className="muted">None on file.</p>}
        <ul>
          {customer.phone_numbers.map((p) => (
            <li key={p.id}>
              {p.phone_number} ({p.phone_type}) {p.is_primary && <strong>primary</strong>}
            </li>
          ))}
        </ul>
      </div>

      <div className="card">
        <div className="section-title">
          <h2>Vehicles</h2>
          <button onClick={() => setShowAddVehicle((v) => !v)}>
            {showAddVehicle ? "Cancel" : "Add Vehicle"}
          </button>
        </div>
        {showAddVehicle && (
          <form onSubmit={addVehicle} style={{ marginBottom: 16 }}>
            <div className="field-row">
              <div className="field">
                <label>VIN</label>
                <input value={vin} onChange={(e) => setVin(e.target.value)} maxLength={17} />
              </div>
              <div className="field">
                <label>Year</label>
                <input value={year} onChange={(e) => setYear(e.target.value)} />
              </div>
              <div className="field">
                <label>Make</label>
                <input value={make} onChange={(e) => setMake(e.target.value)} />
              </div>
              <div className="field">
                <label>Model</label>
                <input value={model} onChange={(e) => setModel(e.target.value)} />
              </div>
            </div>
            <button className="primary" type="submit">
              Create Vehicle
            </button>
          </form>
        )}
        <table>
          <thead>
            <tr>
              <th>Vehicle</th>
              <th>VIN</th>
              <th>Plate</th>
              <th>Mileage</th>
            </tr>
          </thead>
          <tbody>
            {vehicles.map((v) => (
              <tr key={v.id} className="clickable" onClick={() => navigate(`/vehicles/${v.id}`)}>
                <td>{vehicleName(v)}</td>
                <td>{v.vin || "—"}</td>
                <td>{v.license_plate || "—"}</td>
                <td>{v.current_mileage ?? "—"}</td>
              </tr>
            ))}
            {vehicles.length === 0 && (
              <tr>
                <td colSpan={4} className="muted">
                  No vehicles on file.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
