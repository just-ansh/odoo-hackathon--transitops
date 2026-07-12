import { useEffect, useState } from 'react';
import { getDashboardKPIs } from '@/lib/api';
import { AppShell, PageHeader } from '@/components/AppShell';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import {
  Truck,
  CheckCircle2,
  Wrench,
  Route as RouteIcon,
  Clock,
  UserCheck,
  Gauge,
  TrendingUp,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

interface KPIs {
  active_vehicles: number;
  available_vehicles: number;
  vehicles_in_maintenance: number;
  active_trips: number;
  pending_trips: number;
  drivers_on_duty: number;
  fleet_utilization_pct: number;
  weekly_trips?: { day: string; trips: number }[];
  monthly_revenue?: { month: string; revenue: number }[];
}

const defaultKPIs: KPIs = {
  active_vehicles: 0,
  available_vehicles: 0,
  vehicles_in_maintenance: 0,
  active_trips: 0,
  pending_trips: 0,
  drivers_on_duty: 0,
  fleet_utilization_pct: 0,
  weekly_trips: [
    { day: 'Mon', trips: 12 },
    { day: 'Tue', trips: 18 },
    { day: 'Wed', trips: 15 },
    { day: 'Thu', trips: 22 },
    { day: 'Fri', trips: 28 },
    { day: 'Sat', trips: 19 },
    { day: 'Sun', trips: 9 },
  ],
  monthly_revenue: [
    { month: 'Jan', revenue: 42000 },
    { month: 'Feb', revenue: 51000 },
    { month: 'Mar', revenue: 48500 },
    { month: 'Apr', revenue: 61000 },
    { month: 'May', revenue: 72000 },
    { month: 'Jun', revenue: 68500 },
  ],
};

function KpiCard({
  label,
  value,
  icon: Icon,
  accent,
  hint,
}: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  accent: string;
  hint?: string;
}) {
  return (
    <Card className="group relative overflow-hidden border-slate-200/70 transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-indigo-500/5 dark:border-slate-800">
      <div
        className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${accent} opacity-80`}
      />
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

export default function DashboardPage() {
  const [filters, setFilters] = useState({ type: 'all', status: 'all', region: 'all' });
  const [kpis, setKpis] = useState<KPIs>(defaultKPIs);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const params: Record<string, string> = {};
    if (filters.type !== 'all') params.type = filters.type;
    if (filters.status !== 'all') params.status = filters.status;
    if (filters.region !== 'all') params.region = filters.region;
    getDashboardKPIs(params)
      .then((data: any) => {
        if (cancelled) return;
        setKpis({ ...defaultKPIs, ...(data?.data ?? {}) });
      })
      .catch(() => {})
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [filters]);

  return (
    <AppShell>
      <PageHeader
        title="Fleet Command Center"
        description="Real-time operations, utilization, and revenue signals across your fleet."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Select value={filters.type} onValueChange={(v) => setFilters((f) => ({ ...f, type: v }))}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="Truck">Truck</SelectItem>
                <SelectItem value="Van">Van</SelectItem>
                <SelectItem value="Trailer">Trailer</SelectItem>
                <SelectItem value="Refrigerated">Refrigerated</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={filters.status}
              onValueChange={(v) => setFilters((f) => ({ ...f, status: v }))}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="Available">Available</SelectItem>
                <SelectItem value="On Trip">On Trip</SelectItem>
                <SelectItem value="In Shop">In Shop</SelectItem>
                <SelectItem value="Retired">Retired</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={filters.region}
              onValueChange={(v) => setFilters((f) => ({ ...f, region: v }))}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Region" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Regions</SelectItem>
                <SelectItem value="North">North</SelectItem>
                <SelectItem value="South">South</SelectItem>
                <SelectItem value="East">East</SelectItem>
                <SelectItem value="West">West</SelectItem>
              </SelectContent>
            </Select>
          </div>
        }
      />

      <div className={`grid gap-4 sm:grid-cols-2 lg:grid-cols-4 ${loading ? 'opacity-70' : ''}`}>
        <KpiCard
          label="Active Vehicles"
          value={kpis.active_vehicles}
          icon={Truck}
          accent="from-indigo-500 to-violet-600"
          hint="Currently deployed"
        />
        <KpiCard
          label="Available"
          value={kpis.available_vehicles}
          icon={CheckCircle2}
          accent="from-emerald-500 to-teal-600"
          hint="Ready to dispatch"
        />
        <KpiCard
          label="In Maintenance"
          value={kpis.vehicles_in_maintenance}
          icon={Wrench}
          accent="from-amber-500 to-orange-500"
          hint="Under repair"
        />
        <KpiCard
          label="Drivers On Duty"
          value={kpis.drivers_on_duty}
          icon={UserCheck}
          accent="from-sky-500 to-cyan-600"
          hint="Live drivers"
        />
        <KpiCard
          label="Active Trips"
          value={kpis.active_trips}
          icon={RouteIcon}
          accent="from-fuchsia-500 to-pink-600"
          hint="In transit"
        />
        <KpiCard
          label="Pending Trips"
          value={kpis.pending_trips}
          icon={Clock}
          accent="from-amber-500 to-rose-500"
          hint="Awaiting dispatch"
        />
        <Card className="sm:col-span-2 border-slate-200/70 dark:border-slate-800">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div>
                <CardDescription className="text-xs font-medium uppercase tracking-wider">
                  Fleet Utilization
                </CardDescription>
                <div className="mt-2 text-3xl font-bold">
                  {Number(kpis.fleet_utilization_pct ?? 0).toFixed(1)}%
                </div>
              </div>
              <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white">
                <Gauge className="h-4 w-4" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Progress value={Number(kpis.fleet_utilization_pct ?? 0)} className="h-2" />
            <p className="mt-2 text-xs text-slate-500">
              Higher utilization means better ROI. Aim for 70%+ sustained.
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card className="border-slate-200/70 dark:border-slate-800">
          <CardHeader>
            <CardTitle className="text-base">Trips Last 7 Days</CardTitle>
            <CardDescription>Dispatched trip volume</CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={kpis.weekly_trips ?? []}>
                <defs>
                  <linearGradient id="barGrad" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="oklch(0.55 0.22 275)" />
                    <stop offset="100%" stopColor="oklch(0.65 0.18 295)" />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis dataKey="day" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="trips" fill="url(#barGrad)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card className="border-slate-200/70 dark:border-slate-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              Monthly Revenue <TrendingUp className="h-4 w-4 text-emerald-500" />
            </CardTitle>
            <CardDescription>Gross trip revenue</CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={kpis.monthly_revenue ?? []}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="revenue"
                  stroke="oklch(0.55 0.22 275)"
                  strokeWidth={3}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
