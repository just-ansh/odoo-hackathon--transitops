import { Outlet, Link } from "react-router-dom";

export default function AppShell() {
  return (
    <div className="flex min-h-screen">
      <aside className="w-56 border-r p-4 space-y-2">
        <Link to="/dashboard" className="block">Dashboard</Link>
        <Link to="/vehicles" className="block">Vehicles</Link>
        <Link to="/drivers" className="block">Drivers</Link>
        <Link to="/trips" className="block">Trips</Link>
        <Link to="/maintenance" className="block">Maintenance</Link>
        <Link to="/fuel-expenses" className="block">Fuel & Expenses</Link>
        <Link to="/reports" className="block">Reports</Link>
      </aside>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}