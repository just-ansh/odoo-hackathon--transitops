import { useEffect, useMemo, useState } from 'react';
import { AppShell, PageHeader } from '@/components/AppShell';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  getExpenses,
  getFleetRoi,
  getFuelLogs,
  getMaintenanceLogs,
  getTrips,
  getVehicleRoiBreakdown,
  getVehicles,
} from '@/lib/api';
import type { FuelLog, MaintenanceLog, Trip, Vehicle, Expense } from '@/types';
import { Download, TrendingUp, Gauge, DollarSign, FileText } from 'lucide-react';
import { toast } from 'sonner';

interface FleetRoi {
  revenue: number;
  fuel_cost: number;
  maintenance_cost: number;
  other_expense: number;
  acquisition_cost: number;
  roi: number;
  fuel_efficiency: number;
  fleet_utilization: number;
}
interface VehicleRoiRow {
  vehicle_id: number;
  registration_number?: string;
  name_model?: string;
  revenue: number;
  fuel_cost: number;
  maintenance_cost: number;
  other_expense: number;
  acquisition_cost: number;
  roi: number;
}

function safeDiv(a: number, b: number) {
  return b === 0 ? 0 : a / b;
}

export default function ReportsPage() {
  const [fleet, setFleet] = useState<FleetRoi | null>(null);
  const [rows, setRows] = useState<VehicleRoiRow[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [startIndex, setStartIndex] = useState(0);
  const pageSize = 12;

  useEffect(() => {
    (async () => {
      const [vs, ts, fs, ms, ex] = await Promise.all([
        getVehicles().catch(() => []),
        getTrips().catch(() => []),
        getFuelLogs().catch(() => []),
        getMaintenanceLogs().catch(() => []),
        getExpenses().catch(() => []),
      ]);
      const vehiclesData: Vehicle[] = Array.isArray(vs) ? vs : (vs as any)?.data ?? [];
      setVehicles(vehiclesData);

      let fleetData: FleetRoi | null = null;
      let vehicleRoi: VehicleRoiRow[] = [];
      try {
        const res = await getFleetRoi();
        const metrics = res.data?.roi_metrics;
        if (metrics) {
          fleetData = {
            revenue: Number(metrics.total_revenue),
            fuel_cost: Number(metrics.total_fuel_cost),
            maintenance_cost: Number(metrics.total_maintenance_cost),
            other_expense: Number(metrics.total_other_expense_cost ?? 0),
            acquisition_cost: Number(metrics.total_acquisition_cost),
            roi: Number(metrics.fleet_roi),
            fuel_efficiency: 0,
            fleet_utilization: 0,
          };
        }
      } catch {
        /* fall through to derive */
      }
      try {
        const res = await getVehicleRoiBreakdown();
        const breakdown = res.data?.vehicle_roi_breakdown;
        if (Array.isArray(breakdown)) {
          vehicleRoi = breakdown.map((b: any) => ({
            vehicle_id: b.vehicle_id,
            registration_number: b.registration_number,
            name_model: b.name_model,
            revenue: Number(b.total_revenue),
            fuel_cost: Number(b.total_fuel),
            maintenance_cost: Number(b.total_maintenance),
            other_expense: Number(b.total_other_expense ?? 0),
            acquisition_cost: Number(b.acquisition_cost),
            roi: Number(b.roi),
          }));
        }
      } catch {
        /* fall through */
      }

      // Derive if backend didn't respond
      const tripsData: Trip[] = Array.isArray(ts) ? ts : (ts as any)?.data ?? [];
      const fuelData: FuelLog[] = Array.isArray(fs) ? fs : (fs as any)?.data ?? [];
      const maintData: MaintenanceLog[] = Array.isArray(ms) ? ms : (ms as any)?.data ?? [];
      const expensesData: Expense[] = Array.isArray(ex) ? ex : (ex as any)?.data ?? [];

      if (!fleetData) {
        const revenue = tripsData
          .filter((t) => t.status === 'Completed')
          .reduce((s, t) => s + (t.revenue ?? 0), 0);
        const fuel_cost = fuelData.reduce((s, f) => s + f.cost, 0);
        const maint_log_cost = maintData.reduce((s, m) => s + (m.cost ?? 0), 0);
        const maint_exp_cost = expensesData.filter((e) => e.type === 'Maintenance').reduce((s, e) => s + e.amount, 0);
        const maintenance_cost = maint_log_cost + maint_exp_cost;
        const other_expense = expensesData.filter((e) => e.type !== 'Maintenance').reduce((s, e) => s + e.amount, 0);
        const acquisition_cost = vehiclesData.reduce((s, v) => s + v.acquisition_cost, 0);
        const completed = tripsData.filter(
          (t) => t.status === 'Completed' && t.fuel_consumed_liters,
        );
        const dist = completed.reduce((s, t) => s + (t.planned_distance ?? 0), 0);
        const liters = completed.reduce((s, t) => s + (t.fuel_consumed_liters ?? 0), 0);
        const onTripOrRunning = vehiclesData.filter(
          (v) => v.status === 'On Trip' || v.status === 'Available',
        ).length;
        fleetData = {
          revenue,
          fuel_cost,
          maintenance_cost,
          other_expense,
          acquisition_cost,
          roi: safeDiv(revenue - fuel_cost - maintenance_cost - other_expense, acquisition_cost),
          fuel_efficiency: safeDiv(dist, liters),
          fleet_utilization: safeDiv(
            vehiclesData.filter((v) => v.status === 'On Trip').length,
            Math.max(onTripOrRunning, 1),
          ) * 100,
        };
      }
      if (vehicleRoi.length === 0) {
        vehicleRoi = vehiclesData.map((v) => {
          const rev = tripsData
            .filter((t) => t.vehicle_id === v.id && t.status === 'Completed')
            .reduce((s, t) => s + t.revenue, 0);
          const fc = fuelData.filter((f) => f.vehicle_id === v.id).reduce((s, f) => s + f.cost, 0);
          const mc = maintData.filter((m) => m.vehicle_id === v.id).reduce((s, m) => s + m.cost, 0);
          const me = expensesData.filter((e) => e.vehicle_id === v.id && e.type === 'Maintenance').reduce((s, e) => s + e.amount, 0);
          const oe = expensesData.filter((e) => e.vehicle_id === v.id && e.type !== 'Maintenance').reduce((s, e) => s + e.amount, 0);
          return {
            vehicle_id: v.id,
            registration_number: v.registration_number,
            name_model: v.name_model,
            revenue: rev,
            fuel_cost: fc,
            maintenance_cost: mc + me,
            other_expense: oe,
            acquisition_cost: v.acquisition_cost,
            roi: safeDiv(rev - fc - (mc + me) - oe, v.acquisition_cost),
          };
        });
      }
      setFleet(fleetData);
      setRows(vehicleRoi);
    })();
  }, []);

  const chartData = useMemo(
    () =>
      rows.slice(startIndex, startIndex + pageSize).map((r) => ({
        name: r.registration_number ?? `#${r.vehicle_id}`,
        roi: Number((r.roi * 100).toFixed(2)),
      })),
    [rows, startIndex],
  );

  const exportCsv = () => {
    if (!fleet) {
      toast.error('No report data yet.');
      return;
    }
    const header = [
      'Vehicle',
      'Model',
      'Revenue',
      'Fuel Cost',
      'Maintenance Cost',
      'Other Expenses',
      'Operational Cost',
      'Acquisition Cost',
      'ROI %',
    ];
    const body = rows.map((r) => [
      r.registration_number ?? r.vehicle_id,
      r.name_model ?? '',
      r.revenue.toFixed(2),
      r.fuel_cost.toFixed(2),
      r.maintenance_cost.toFixed(2),
      r.other_expense.toFixed(2),
      (r.fuel_cost + r.maintenance_cost + r.other_expense).toFixed(2),
      r.acquisition_cost.toFixed(2),
      (r.roi * 100).toFixed(2),
    ]);
    const totals = [
      'TOTAL',
      '',
      fleet.revenue.toFixed(2),
      fleet.fuel_cost.toFixed(2),
      fleet.maintenance_cost.toFixed(2),
      fleet.other_expense.toFixed(2),
      (fleet.fuel_cost + fleet.maintenance_cost + fleet.other_expense).toFixed(2),
      fleet.acquisition_cost.toFixed(2),
      (fleet.roi * 100).toFixed(2),
    ];
    const csv = [header, ...body, totals]
      .map((r) => r.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','))
      .join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transitops-report-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Report exported');
  };

  const printPdf = () => {
    window.print();
  };

  return (
    <AppShell>
      <PageHeader
        title="Reports & ROI"
        description="Financial performance, fuel efficiency, and utilization."
        actions={
          <div className="flex gap-2">
            <Button onClick={exportCsv} variant="outline" className="gap-2">
              <Download className="h-4 w-4" /> Export CSV
            </Button>
            <Button onClick={printPdf} className="gap-2">
              <FileText className="h-4 w-4" /> Print PDF
            </Button>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <SummaryCard
          label="Fleet ROI"
          value={fleet ? `${(fleet.roi * 100).toFixed(1)}%` : '—'}
          icon={TrendingUp}
          accent="from-emerald-500 to-teal-600"
          hint="(Revenue − Fuel − Maint.) / Acquisition"
        />
        <SummaryCard
          label="Fuel Efficiency"
          value={fleet ? `${fleet.fuel_efficiency.toFixed(2)} km/L` : '—'}
          icon={Gauge}
          accent="from-indigo-500 to-violet-600"
          hint="Completed trips only"
        />
        <SummaryCard
          label="Fleet Utilization"
          value={fleet ? `${fleet.fleet_utilization.toFixed(1)}%` : '—'}
          icon={Gauge}
          accent="from-amber-500 to-orange-500"
          hint="On Trip / (On Trip + Available)"
        />
        <SummaryCard
          label="Operational Cost"
          value={fleet ? `$${(fleet.fuel_cost + fleet.maintenance_cost + fleet.other_expense).toLocaleString()}` : '—'}
          icon={DollarSign}
          accent="from-rose-500 to-red-600"
          hint="Fuel + Maint. + Expenses"
        />
        <SummaryCard
          label="Gross Revenue"
          value={fleet ? `$${fleet.revenue.toLocaleString()}` : '—'}
          icon={DollarSign}
          accent="from-fuchsia-500 to-pink-600"
          hint="Completed trips"
        />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <Card className="border-slate-200/70 lg:col-span-2 dark:border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle className="text-base">ROI by Vehicle</CardTitle>
              <CardDescription>Top performing assets comparison chart</CardDescription>
            </div>
            {rows.length > pageSize && (
              <div className="flex items-center gap-3">
                <span className="text-[11px] text-slate-500">
                  Vehicles {startIndex + 1}–{Math.min(startIndex + pageSize, rows.length)} of {rows.length}
                </span>
                <input
                  type="range"
                  min="0"
                  max={rows.length - pageSize}
                  value={startIndex}
                  onChange={(e) => setStartIndex(Number(e.target.value))}
                  className="h-1 cursor-pointer rounded-lg bg-slate-200 accent-indigo-600 dark:bg-slate-700 w-24"
                />
              </div>
            )}
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-15} height={50} />
                <YAxis tick={{ fontSize: 12 }} unit="%" />
                <Tooltip
                  formatter={(value: any) => [`${value}%`, 'ROI']}
                  contentStyle={{
                    backgroundColor: 'var(--card)',
                    borderColor: 'var(--border)',
                    borderRadius: '0.5rem',
                    color: 'var(--foreground)'
                  }}
                  itemStyle={{ color: 'var(--foreground)' }}
                  labelStyle={{ color: 'var(--muted-foreground)' }}
                />
                <Bar dataKey="roi" radius={[6, 6, 0, 0]}>
                  {chartData.map((d, i) => (
                    <Cell
                      key={i}
                      fill={d.roi >= 0 ? 'oklch(0.68 0.16 165)' : 'oklch(0.65 0.22 25)'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="border-slate-200/70 dark:border-slate-800">
          <CardHeader>
            <CardTitle className="text-base">Cost Breakdown</CardTitle>
            <CardDescription>Fleet totals</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {fleet && (
              <>
                <Row label="Revenue" value={fleet.revenue} tone="text-emerald-600" />
                <Row label="Fuel" value={fleet.fuel_cost} tone="text-indigo-600" />
                <Row label="Maintenance" value={fleet.maintenance_cost} tone="text-amber-600" />
                <Row label="Other Expenses" value={fleet.other_expense} tone="text-purple-600" />
                <Row label="Acquisition" value={fleet.acquisition_cost} tone="text-slate-600" />
                <div className="mt-2 rounded-lg bg-gradient-to-br from-indigo-500/10 to-violet-500/5 p-3">
                  <div className="text-xs uppercase tracking-widest text-slate-500">
                    Net Profit
                  </div>
                  <div className="mt-1 text-2xl font-bold">
                    $
                    {(
                      fleet.revenue -
                      fleet.fuel_cost -
                      fleet.maintenance_cost -
                      fleet.other_expense
                    ).toLocaleString()}
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6 border-slate-200/70 dark:border-slate-800">
        <CardHeader>
          <CardTitle className="text-base">Per-Vehicle Breakdown</CardTitle>
          <CardDescription>
            ROI = (Revenue − Fuel − Maintenance) / Acquisition Cost
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-lg border border-slate-200/70 dark:border-slate-800">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Vehicle</TableHead>
                  <TableHead>Model</TableHead>
                  <TableHead>Revenue</TableHead>
                  <TableHead>Fuel</TableHead>
                  <TableHead>Maintenance</TableHead>
                  <TableHead>Other Expenses</TableHead>
                  <TableHead>Operational Cost</TableHead>
                  <TableHead>Acquisition</TableHead>
                  <TableHead>ROI</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} className="py-10 text-center text-sm text-slate-500">
                      No data available yet.
                    </TableCell>
                  </TableRow>
                ) : (
                  rows.map((r) => (
                    <TableRow
                      key={r.vehicle_id}
                      className="hover:bg-slate-50/60 dark:hover:bg-slate-900/40"
                    >
                      <TableCell className="font-mono text-xs font-medium">
                        {r.registration_number ??
                          vehicles.find((v) => v.id === r.vehicle_id)?.registration_number ??
                          `#${r.vehicle_id}`}
                      </TableCell>
                      <TableCell>
                        {r.name_model ??
                          vehicles.find((v) => v.id === r.vehicle_id)?.name_model ??
                          '—'}
                      </TableCell>
                      <TableCell>${r.revenue.toLocaleString()}</TableCell>
                      <TableCell>${r.fuel_cost.toLocaleString()}</TableCell>
                      <TableCell>${r.maintenance_cost.toLocaleString()}</TableCell>
                      <TableCell>${r.other_expense.toLocaleString()}</TableCell>
                      <TableCell className="font-semibold">${(r.fuel_cost + r.maintenance_cost + r.other_expense).toLocaleString()}</TableCell>
                      <TableCell>${r.acquisition_cost.toLocaleString()}</TableCell>
                      <TableCell
                        className={
                          r.roi >= 0 ? 'font-semibold text-emerald-600' : 'font-semibold text-rose-600'
                        }
                      >
                        {(r.roi * 100).toFixed(1)}%
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </AppShell>
  );
}

function SummaryCard({
  label,
  value,
  icon: Icon,
  accent,
  hint,
}: {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  accent: string;
  hint?: string;
}) {
  return (
    <Card className="group relative overflow-hidden border-slate-200/70 transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-indigo-500/5 dark:border-slate-800">
      <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${accent}`} />
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardDescription className="text-xs font-medium uppercase tracking-wider">
          {label}
        </CardDescription>
        <div
          className={`grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br ${accent} text-white shadow-sm transition-transform group-hover:scale-110`}
        >
          <Icon className="h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold tracking-tight">{value}</div>
        {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
      </CardContent>
    </Card>
  );
}

function Row({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-slate-500">{label}</span>
      <span className={`font-semibold ${tone}`}>${value.toLocaleString()}</span>
    </div>
  );
}
