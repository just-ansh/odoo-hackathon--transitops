import { useEffect, useMemo, useState } from 'react';
import { AppShell, PageHeader } from '@/components/AppShell';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Card, CardContent } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { StatusBadge } from '@/components/StatusBadge';
import {
  cancelTrip,
  completeTrip,
  createTrip,
  dispatchTrip,
  getDrivers,
  getTrips,
  getVehicles,
} from '@/lib/api';
import type { Driver, Trip, Vehicle } from '@/types';
import { roleCan, useAuthStore } from '@/store/authStore';
import {
  AlertTriangle,
  CheckCircle2,
  Lock,
  Plus,
  Send,
  XCircle,
} from 'lucide-react';
import { toast } from 'sonner';

const STATUSES: Trip['status'][] = ['Draft', 'Dispatched', 'Completed', 'Cancelled'];

interface TripFormState {
  source: string;
  destination: string;
  vehicle_id: number | null;
  driver_id: number | null;
  cargo_weight: number;
  planned_distance: number;
  revenue: number;
}
const emptyTrip: TripFormState = {
  source: '',
  destination: '',
  vehicle_id: null,
  driver_id: null,
  cargo_weight: 0,
  planned_distance: 0,
  revenue: 0,
};

const isDriverLicenseExpired = (d: Driver) => new Date(d.license_expiry_date) < new Date();

export default function TripsPage() {
  const role = useAuthStore((s) => s.user?.role);
  const canCreate = roleCan.createTrips(role);
  const canComplete = roleCan.completeTrips(role);

  const [trips, setTrips] = useState<Trip[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [statusFilter, setStatusFilter] = useState('all');

  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState<TripFormState>(emptyTrip);

  const [completeTripState, setCompleteTripState] = useState<Trip | null>(null);
  const [completeForm, setCompleteForm] = useState({ final_odometer: 0, fuel_consumed_liters: 0 });

  const load = () => {
    Promise.all([getTrips(), getVehicles(), getDrivers()])
      .then(([t, v, d]: any) => {
        setTrips(Array.isArray(t) ? t : t?.data ?? []);
        setVehicles(Array.isArray(v) ? v : v?.data ?? []);
        setDrivers(Array.isArray(d) ? d : d?.data ?? []);
      })
      .catch(() => {});
  };
  useEffect(() => {
    load();
  }, []);

  const availableVehicles = vehicles.filter((v) => v.status === 'Available');
  const availableDrivers = drivers.filter((d) => d.status === 'Available');
  const vehiclesById = useMemo(() => new Map(vehicles.map((v) => [v.id, v])), [vehicles]);
  const driversById = useMemo(() => new Map(drivers.map((d) => [d.id, d])), [drivers]);

  const selectedVehicle = form.vehicle_id ? vehiclesById.get(form.vehicle_id) ?? null : null;
  const selectedDriver = form.driver_id ? driversById.get(form.driver_id) ?? null : null;
  const licenseWarning = selectedDriver && isDriverLicenseExpired(selectedDriver);
  const overCapacity =
    selectedVehicle && form.cargo_weight > selectedVehicle.max_load_capacity;

  const filtered = statusFilter === 'all' ? trips : trips.filter((t) => t.status === statusFilter);

  const submitTrip = async () => {
    if (!form.source.trim() || !form.destination.trim()) {
      toast.error('Source and destination are required.');
      return;
    }
    if (!form.vehicle_id || !form.driver_id) {
      toast.error('Select a vehicle and a driver.');
      return;
    }
    if (licenseWarning) {
      toast.error('Driver license has expired. Choose another driver.');
      return;
    }
    if (overCapacity) {
      toast.error('Cargo weight exceeds vehicle capacity.');
      return;
    }
    try {
      await createTrip({ ...form, status: 'Draft' });
      toast.success('Trip created as Draft');
      setCreateOpen(false);
      setForm(emptyTrip);
      load();
    } catch (e: any) {
      toast.error(e?.response?.data?.message ?? 'Failed to create trip');
    }
  };

  const doDispatch = async (t: Trip) => {
    try {
      await dispatchTrip(t.id);
      toast.success(`Trip #${t.id} dispatched`);
      load();
    } catch (e: any) {
      toast.error(e?.response?.data?.message ?? 'Dispatch failed');
    }
  };
  const doCancel = async (t: Trip) => {
    try {
      await cancelTrip(t.id);
      toast.success(`Trip #${t.id} cancelled`);
      load();
    } catch (e: any) {
      toast.error(e?.response?.data?.message ?? 'Cancel failed');
    }
  };
  const openComplete = (t: Trip) => {
    const v = vehiclesById.get(t.vehicle_id);
    setCompleteForm({ final_odometer: v?.odometer ?? 0, fuel_consumed_liters: 0 });
    setCompleteTripState(t);
  };
  const submitComplete = async () => {
    if (!completeTripState) return;
    const v = vehiclesById.get(completeTripState.vehicle_id);
    if (v && completeForm.final_odometer < v.odometer) {
      toast.error(`Final odometer must be ≥ current odometer (${v.odometer} km).`);
      return;
    }
    if (completeForm.fuel_consumed_liters <= 0) {
      toast.error('Fuel consumed must be greater than 0.');
      return;
    }
    try {
      await completeTrip(completeTripState.id, completeForm);
      toast.success(`Trip #${completeTripState.id} completed`);
      setCompleteTripState(null);
      load();
    } catch (e: any) {
      toast.error(e?.response?.data?.message ?? 'Complete failed');
    }
  };

  return (
    <AppShell>
      <PageHeader
        title="Trip Dispatch"
        description="Schedule, dispatch, and close out trips across your fleet."
        actions={
          <div className="flex items-center gap-2">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[160px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                {STATUSES.map((s) => (
                  <SelectItem key={s} value={s}>
                    {s}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {canCreate ? (
              <Button onClick={() => setCreateOpen(true)} className="gap-2">
                <Plus className="h-4 w-4" /> New Trip
              </Button>
            ) : (
              <div className="flex items-center gap-1.5 text-xs text-slate-500">
                <Lock className="h-3.5 w-3.5" /> Read-only for {role}
              </div>
            )}
          </div>
        }
      />

      <Card className="border-slate-200/70 dark:border-slate-800">
        <CardContent className="p-4 sm:p-6">
          <div className="overflow-x-auto rounded-lg border border-slate-200/70 dark:border-slate-800">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>#</TableHead>
                  <TableHead>Route</TableHead>
                  <TableHead>Vehicle</TableHead>
                  <TableHead>Driver</TableHead>
                  <TableHead>Cargo (kg)</TableHead>
                  <TableHead>Planned (km)</TableHead>
                  <TableHead>Revenue</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} className="py-10 text-center text-sm text-slate-500">
                      No trips found.
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.map((t) => {
                    const v = vehiclesById.get(t.vehicle_id);
                    const d = driversById.get(t.driver_id);
                    return (
                      <TableRow
                        key={t.id}
                        className="hover:bg-slate-50/60 dark:hover:bg-slate-900/40"
                      >
                        <TableCell className="font-mono text-xs">#{t.id}</TableCell>
                        <TableCell>
                          <div className="font-medium">
                            {t.source} → {t.destination}
                          </div>
                        </TableCell>
                        <TableCell className="text-sm">
                          {v ? `${v.registration_number}` : `#${t.vehicle_id}`}
                        </TableCell>
                        <TableCell className="text-sm">{d?.name ?? `#${t.driver_id}`}</TableCell>
                        <TableCell>{t.cargo_weight.toLocaleString()}</TableCell>
                        <TableCell>{t.planned_distance.toLocaleString()}</TableCell>
                        <TableCell>${t.revenue.toLocaleString()}</TableCell>
                        <TableCell>
                          <StatusBadge status={t.status} />
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex flex-wrap justify-end gap-1">
                            {t.status === 'Draft' && canCreate && (
                              <Button size="sm" variant="secondary" onClick={() => doDispatch(t)}>
                                <Send className="mr-1 h-3.5 w-3.5" /> Dispatch
                              </Button>
                            )}
                            {t.status === 'Dispatched' && canComplete && (
                              <Button size="sm" onClick={() => openComplete(t)}>
                                <CheckCircle2 className="mr-1 h-3.5 w-3.5" /> Complete
                              </Button>
                            )}
                            {t.status === 'Dispatched' && canCreate && (
                              <Button size="sm" variant="ghost" onClick={() => doCancel(t)}>
                                <XCircle className="mr-1 h-3.5 w-3.5 text-rose-500" /> Cancel
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Create trip */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>New Trip</DialogTitle>
            <DialogDescription>
              Only Available vehicles and drivers can be assigned to a trip.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Source</Label>
              <Input
                value={form.source}
                onChange={(e) => setForm((f) => ({ ...f, source: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Destination</Label>
              <Input
                value={form.destination}
                onChange={(e) => setForm((f) => ({ ...f, destination: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Vehicle (Available only)</Label>
              <Select
                value={form.vehicle_id?.toString() ?? ''}
                onValueChange={(v) => setForm((f) => ({ ...f, vehicle_id: Number(v) }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select vehicle" />
                </SelectTrigger>
                <SelectContent>
                  {availableVehicles.length === 0 ? (
                    <div className="px-2 py-1.5 text-xs text-slate-500">No available vehicles</div>
                  ) : (
                    availableVehicles.map((v) => (
                      <SelectItem key={v.id} value={v.id.toString()}>
                        {v.registration_number} — {v.name_model} ({v.max_load_capacity}kg)
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Driver (Available only)</Label>
              <Select
                value={form.driver_id?.toString() ?? ''}
                onValueChange={(v) => setForm((f) => ({ ...f, driver_id: Number(v) }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select driver" />
                </SelectTrigger>
                <SelectContent>
                  {availableDrivers.length === 0 ? (
                    <div className="px-2 py-1.5 text-xs text-slate-500">No available drivers</div>
                  ) : (
                    availableDrivers.map((d) => (
                      <SelectItem key={d.id} value={d.id.toString()}>
                        {d.name} — {d.license_category}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Cargo Weight (kg)</Label>
              <Input
                type="number"
                value={form.cargo_weight}
                onChange={(e) => setForm((f) => ({ ...f, cargo_weight: Number(e.target.value) }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Planned Distance (km)</Label>
              <Input
                type="number"
                value={form.planned_distance}
                onChange={(e) =>
                  setForm((f) => ({ ...f, planned_distance: Number(e.target.value) }))
                }
              />
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label>Revenue ($)</Label>
              <Input
                type="number"
                value={form.revenue}
                onChange={(e) => setForm((f) => ({ ...f, revenue: Number(e.target.value) }))}
              />
            </div>
          </div>

          {licenseWarning && (
            <Alert className="border-rose-200 bg-rose-50 dark:border-rose-900/50 dark:bg-rose-950/30">
              <AlertTriangle className="h-4 w-4 text-rose-600" />
              <AlertTitle className="text-rose-700 dark:text-rose-300">
                Driver license expired
              </AlertTitle>
              <AlertDescription className="text-rose-600/80 dark:text-rose-300/80">
                {selectedDriver?.name}'s license expired on{' '}
                {new Date(selectedDriver!.license_expiry_date).toLocaleDateString()}.
              </AlertDescription>
            </Alert>
          )}
          {overCapacity && (
            <Alert className="border-amber-200 bg-amber-50 dark:border-amber-900/50 dark:bg-amber-950/30">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              <AlertTitle className="text-amber-700 dark:text-amber-300">
                Over capacity
              </AlertTitle>
              <AlertDescription className="text-amber-600/80 dark:text-amber-300/80">
                Cargo ({form.cargo_weight}kg) exceeds vehicle capacity (
                {selectedVehicle?.max_load_capacity}kg).
              </AlertDescription>
            </Alert>
          )}

          <DialogFooter>
            <Button variant="ghost" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button onClick={submitTrip} disabled={!!licenseWarning || !!overCapacity}>
              Create Draft
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Complete trip */}
      <Dialog
        open={completeTripState != null}
        onOpenChange={(o) => !o && setCompleteTripState(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Complete Trip #{completeTripState?.id}</DialogTitle>
            <DialogDescription>
              Record final odometer and fuel consumed to close this trip.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {completeTripState && (
              <div className="rounded-lg border border-slate-200/70 bg-slate-50 p-3 text-sm dark:border-slate-800 dark:bg-slate-900/50">
                <div className="font-medium">
                  {completeTripState.source} → {completeTripState.destination}
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  Vehicle current odometer:{' '}
                  <span className="font-mono">
                    {vehiclesById.get(completeTripState.vehicle_id)?.odometer.toLocaleString() ?? '?'} km
                  </span>
                </div>
              </div>
            )}
            <div className="space-y-2">
              <Label>Final Odometer (km)</Label>
              <Input
                type="number"
                value={completeForm.final_odometer}
                onChange={(e) =>
                  setCompleteForm((f) => ({ ...f, final_odometer: Number(e.target.value) }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Fuel Consumed (liters)</Label>
              <Input
                type="number"
                step="0.01"
                value={completeForm.fuel_consumed_liters}
                onChange={(e) =>
                  setCompleteForm((f) => ({
                    ...f,
                    fuel_consumed_liters: Number(e.target.value),
                  }))
                }
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setCompleteTripState(null)}>
              Cancel
            </Button>
            <Button onClick={submitComplete}>Complete Trip</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppShell>
  );
}
