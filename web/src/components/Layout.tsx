import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/customers", label: "Customers" },
  { to: "/vehicles", label: "Vehicles" },
  { to: "/repair-orders", label: "Repair Orders" },
  { to: "/invoices", label: "Invoices" },
  { to: "/parts", label: "Parts" },
  { to: "/suppliers", label: "Suppliers" },
  { to: "/purchase-orders", label: "Purchase Orders" },
  { to: "/reports", label: "Reports" },
];

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <nav className="sidebar">
        <div className="brand">Mechanic Shop Manager</div>
        <ul>
          {links.map((link) => (
            <li key={link.to}>
              <NavLink to={link.to} end={link.end} className={({ isActive }) => (isActive ? "active" : "")}>
                {link.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <main className="content">{children}</main>
    </div>
  );
}
