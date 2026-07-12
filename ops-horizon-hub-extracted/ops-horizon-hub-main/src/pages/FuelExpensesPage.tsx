import { useEffect, useMemo, useState } from 'react';
import { AppShell, PageHeader } from '@/components/AppShell';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
import {
  createExpense,
  createFuelLog,
  getExpenses,
  getFuelLogs,
  getTrips,
  getVehicles,
} from '@/lib/api';
import type { Expense, FuelLog, Trip, Vehicle } from '@/types';
import { roleCan, useAuthStore } from '@/store/authStore';
import { Fuel, Lock, Plus, Receipt } from 'lucide-react';
import { toast } from 'sonner';

const EXPENSE_TYPES: Expense['type'][] = ['Tolls', 'Maintenance', 'Other'];

export default function FuelExpensesPage() {
  const role = useAuthStore((s) => s.user?.role);
  const canEdit = roleCan.manageFinance(role);

  const [fuelLogs, setFuelLogs] = useState<FuelLog[]>([]);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [trips, setTrips] = useState<Trip[]>([]);

  const [fuelOpen, setFuelOpen] = useState(false);
  const [expOpen, setExpOpen] = useState(false);

  const today = new Date().toISOString().slice(0, 10);
  const [fuelForm, setFuelForm] = useState({
    vehicle_id: null as number | null,
    liters: 0,
    cost: 0,
    logged_date: today,
    trip_id: null as number | null,
  });
  const [expForm, setExpForm] = useState({
    vehicle_id: null as number | null,
    type: 'Tolls' as Expense['type'],
    amount: 0,
    description: '',
    logged_date: today,
  });

  const load = () => {
    Promise.all([getFuelLogs(), getExpenses(), getVehicles(), getTrips()])
      .then(([f, e, v, t]: any) => {
        setFuelLogs(Array.isArray(f) ? f : f?.data ?? []);
        setExpenses(Array.isArray(e) ? e : e?.data ?? []);
        setVehicles(Array.isArray(v) ? v : v?.data ?? []);
        setTrips(Array.isArray(t) ? t : t?.data ?? []);
      })
      .catch(() => {});
  };
  useEffect(() => {
    load();
  }, []);

  const vehiclesById = useMemo(() => new Map(vehicles.map((v) => [v.id, v])), [vehicles]);
  const activeTrips = trips.filter((t) => t.status === 'Dispatched' || t.status === 'Draft');

  const submitFuel = async () => {
    if (!fuelForm.vehicle_id || fuelForm.liters <= 0 || fuelForm.cost <= 0) {
      toast.error('Vehicle, liters and cost are required.');
      return;
    }
    try {
      await createFuelLog({
        vehicle_id: fuelForm.vehicle_id,
        liters: fuelForm.liters,
        cost: fuelForm.cost,
        logged_date: fuelForm.logged_date,
        ...(fuelForm.trip_id ? { trip_id: fuelForm.trip_id } : {}),
      });
      toast.success('Fuel log recorded');
      setFuelOpen(false);
      setFuelForm({ vehicle_id: null, liters: 0, cost: 0, logged_date: today, trip_id: null });
      load();
    } catch (e: any) {
      toast.error(e?.response?.data?.message ?? 'Failed to record fuel');
    }
  };

  const submitExpense = async () => {
    if (!expForm.vehicle_id || expForm.amount <= 0) {
      toast.error('Vehicle and amount are required.');
      return;
    }
    try {
      await createExpense({
        vehicle_id: expForm.vehicle_id,
        type: expForm.type,
        amount: expForm.amount,
        description: expForm.description,
        logged_date: expForm.logged_date,
      });
      toast.success('Expense recorded');
      setExpOpen(false);
      setExpForm({
        vehicle_id: null,
        type: 'Tolls',
        amount: 0,
        description: '',
        logged_date: today,
      });
      load();
    } catch (e: any) {
      toast.error(e?.response?.data?.message ?? 'Failed to record expense');
    }
  };

  return (
    <AppShell>
      <PageHeader
        title="Fuel & Expenses"
        description="Record fueling and operating costs by vehicle."
        actions={
          !canEdit && (
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <Lock className="h-3.5 w-3.5" /> Read-only for {role}
            </div>
          )
        }
      />

      <Card className="border-slate-200/70 dark:border-slate-800">
        <CardContent className="p-4 sm:p-6">
          <Tabs defaultValue="fuel">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <TabsList>
                <TabsTrigger value="fuel" className="gap-2">
                  <Fuel className="h-4 w-4" /> Fuel Logs
                </TabsTrigger>
                <TabsTrigger value="expenses" className="gap-2">
                  <Receipt className="h-4 w-4" /> Expenses
                </TabsTrigger>
              </TabsList>
              <div className="flex gap-2">
                {canEdit && (
                  <>
                    <Button variant="secondary" onClick={() => setFuelOpen(true)} className="gap-1">
                      <Plus className="h-4 w-4" /> Fuel
                    </Button>
                    <Button onClick={() => setExpOpen(true)} className="gap-1">
                      <Plus className="h-4 w-4" /> Expense
                    </Button>
                  </>
                )}
              </div>
            </div>

            <TabsContent value="fuel" className="mt-4">
              <div className="overflow-x-auto rounded-lg border border-slate-200/70 dark:border-slate-800">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Vehicle</TableHead>
                      <TableHead>Trip</TableHead>
                      <TableHead>Liters</TableHead>
                      <TableHead>Cost</TableHead>
                      <TableHead>$/L</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fuelLogs.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="py-10 text-center text-sm text-slate-500">
                          No fuel logs yet.
                        </TableCell>
                      </TableRow>
                    ) : (
                      fuelLogs.map((f) => {
                        const v = vehiclesById.get(f.vehicle_id);
                        return (
                          <TableRow
                            key={f.id}
                            className="hover:bg-slate-50/60 dark:hover:bg-slate-900/40"
                          >
                            <TableCell className="text-xs text-slate-500">
                              {new Date(f.logged_date).toLocaleDateString()}
                            </TableCell>
                            <TableCell className="font-medium">
                              {v ? v.registration_number : `#${f.vehicle_id}`}
                            </TableCell>
                            <TableCell className="text-sm">
                              {f.trip_id ? `#${f.trip_id}` : '—'}
                            </TableCell>
                            <TableCell>{f.liters.toFixed(2)}</TableCell>
                            <TableCell>${f.cost.toFixed(2)}</TableCell>
                            <TableCell className="text-slate-500">
                              ${(f.cost / Math.max(f.liters, 0.01)).toFixed(2)}
                            </TableCell>
                          </TableRow>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </div>
            </TabsContent>

            <TabsContent value="expenses" className="mt-4">
              <div className="overflow-x-auto rounded-lg border border-slate-200/70 dark:border-slate-800">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Vehicle</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Description</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {expenses.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} className="py-10 text-center text-sm text-slate-500">
                          No expenses recorded.
                        </TableCell>
                      </TableRow>
                    ) : (
                      expenses.map((e) => {
                        const v = vehiclesById.get(e.vehicle_id);
                        return (
                          <TableRow
                            key={e.id}
                            className="hover:bg-slate-50/60 dark:hover:bg-slate-900/40"
                          >
                            <TableCell className="text-xs text-slate-500">
                              {new Date(e.logged_date).toLocaleDateString()}
                            </TableCell>
                            <TableCell className="font-medium">
                              {v ? v.registration_number : `#${e.vehicle_id}`}
                            </TableCell>
                            <TableCell>
                              <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-300">
                                {e.type}
                              </span>
                            </TableCell>
                            <TableCell>${e.amount.toFixed(2)}</TableCell>
                            <TableCell className="max-w-md text-sm text-slate-600 dark:text-slate-300">
                              {e.description}
                            </TableCell>
                          </TableRow>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Fuel dialog */}
      <Dialog open={fuelOpen} onOpenChange={setFuelOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Fuel Purchase</DialogTitle>
            <DialogDescription>Optionally link the fuel to an active trip.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2 sm:col-span-2">
              <Label>Vehicle</Label>
              <Select
                value={fuelForm.vehicle_id?.toString() ?? ''}
                onValueChange={(v) => setFuelForm((f) => ({ ...f, vehicle_id: Number(v) }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select vehicle" />
                </SelectTrigger>
                <SelectContent>
                  {vehicles.map((v) => (
                    <SelectItem key={v.id} value={v.id.toString()}>
                      {v.registration_number} — {v.name_model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Liters</Label>
              <Input
                type="number"
                step="0.01"
                value={fuelForm.liters}
                onChange={(e) => setFuelForm((f) => ({ ...f, liters: Number(e.target.value) }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Cost ($)</Label>
              <Input
                type="number"
                step="0.01"
                value={fuelForm.cost}
                onChange={(e) => setFuelForm((f) => ({ ...f, cost: Number(e.target.value) }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Date</Label>
              <Input
                type="date"
                value={fuelForm.logged_date}
                onChange={(e) => setFuelForm((f) => ({ ...f, logged_date: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Active Trip (optional)</Label>
              <Select
                value={fuelForm.trip_id?.toString() ?? 'none'}
                onValueChange={(v) =>
                  setFuelForm((f) => ({ ...f, trip_id: v === 'none' ? null : Number(v) }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="None" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  {activeTrips.map((t) => (
                    <SelectItem key={t.id} value={t.id.toString()}>
                      #{t.id} — {t.source} → {t.destination}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setFuelOpen(false)}>
              Cancel
            </Button>
            <Button onClick={submitFuel}>Record Fuel</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Expense dialog */}
      <Dialog open={expOpen} onOpenChange={setExpOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Expense</DialogTitle>
            <DialogDescription>Tolls, ad-hoc maintenance, or other costs.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2 sm:col-span-2">
              <Label>Vehicle</Label>
              <Select
                value={expForm.vehicle_id?.toString() ?? ''}
                onValueChange={(v) => setExpForm((f) => ({ ...f, vehicle_id: Number(v) }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select vehicle" />
                </SelectTrigger>
                <SelectContent>
                  {vehicles.map((v) => (
                    <SelectItem key={v.id} value={v.id.toString()}>
                      {v.registration_number} — {v.name_model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Type</Label>
              <Select
                value={expForm.type}
                onValueChange={(v) => setExpForm((f) => ({ ...f, type: v as Expense['type'] }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {EXPENSE_TYPES.map((t) => (
                    <SelectItem key={t} value={t}>
                      {t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Amount ($)</Label>
              <Input
                type="number"
                step="0.01"
                value={expForm.amount}
                onChange={(e) => setExpForm((f) => ({ ...f, amount: Number(e.target.value) }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Date</Label>
              <Input
                type="date"
                value={expForm.logged_date}
                onChange={(e) => setExpForm((f) => ({ ...f, logged_date: e.target.value }))}
              />
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label>Description</Label>
              <Textarea
                rows={3}
                value={expForm.description}
                onChange={(e) => setExpForm((f) => ({ ...f, description: e.target.value }))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setExpOpen(false)}>
              Cancel
            </Button>
            <Button onClick={submitExpense}>Record Expense</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppShell>
  );
}
