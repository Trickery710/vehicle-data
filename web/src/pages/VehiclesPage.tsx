import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ErrorBanner from "../components/ErrorBanner";
import { vehiclesApi } from "../api/resources";
import type { Vehicle } from "../api/types";

function vehicleName(v: Vehicle): string {
  return [v.year, v.make, v.model].filter(Boolean).join(" ") || `Vehicle #${v.id}`;
}

export default function VehiclesPage() {
  const [items, setItems] = useState<Vehicle[]>([]);
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    vehiclesApi
      .list(q || undefined)
      .then((res) => setItems(res.items))
      .catch((err) => setError(err.message));
  }, [q]);

  return (
    <div>
      <div className="page-header">
        <h1>Vehicles</h1>
      </div>
      <ErrorBanner message={error} />
      <p className="muted">To add a vehicle, open the owning customer and use "Add Vehicle".</p>

      <div className="toolbar">
        <input
          placeholder="Search VIN/plate/make/model/color…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          style={{ minWidth: 280 }}
        />
      </div>

      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>Vehicle</th>
              <th>VIN</th>
              <th>Plate</th>
              <th>Mileage</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((v) => (
              <tr key={v.id} className="clickable" onClick={() => navigate(`/vehicles/${v.id}`)}>
                <td>{vehicleName(v)}</td>
                <td>{v.vin || "—"}</td>
                <td>{v.license_plate || "—"}</td>
                <td>{v.current_mileage ?? "—"}</td>
                <td>{v.is_active ? "Active" : "Inactive"}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={5} className="muted">
                  No vehicles found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
