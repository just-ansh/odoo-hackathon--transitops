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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { StatusBadge } from '@/components/StatusBadge';
import {
  createVehicle,
  deleteVehicle,
  getVehicles,
  updateVehicle,
} from '@/lib/api';
import type { Vehicle } from '@/types';
import { roleCan, useAuthStore } from '@/store/authStore';
import { Plus, Pencil, Trash2, Search, Lock } from 'lucide-react';
import { toast } from 'sonner';

const VEHICLE_TYPES = ['Truck', 'Van', 'Trailer', 'Refrigerated', 'Tanker'];
const STATUSES: Vehicle['status'][] = ['Available', 'On Trip', 'In Shop', 'Retired'];

type FormState = {
  registration_number: string;
  name_model: string;
  type: string;
  max_load_capacity: string;
  odometer: string;
  acquisition_cost: string;
  status: Vehicle['status'];
  region: string;
};
const emptyForm: FormState = {
  registration_number: '',
  name_model: '',
  type: 'Truck',
  max_load_capacity: '',
  odometer: '',
  acquisition_cost: '',
  status: 'Available',
  region: '',
};

export default function VehiclesPage() {
  const role = useAuthStore((s) => s.user?.role);
  const canEdit = roleCan.manageFleet(role);

  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [sortBy, setSortBy] = useState<keyof Vehicle>('registration_number');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [editing, setEditing] = useState<Vehicle | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const load = () =>
    getVehicles()
      .then((d: any) => setVehicles(Array.isArray(d) ? d : d?.data ?? []))
      .catch(() => setVehicles([]));

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => {
    const s = search.toLowerCase();
    return vehicles
      .filter(
        (v) =>
          (statusFilter === 'all' || v.status === statusFilter) &&
          (typeFilter === 'all' || v.type === typeFilter) &&
          (!s ||
            v.registration_number.toLowerCase().includes(s) ||
            v.name_model.toLowerCase().includes(s) ||
            (v.region ?? '').toLowerCase().includes(s)),
      )
      .sort((a, b) => {
        const av = a[sortBy];
        const bv = b[sortBy];
        if (av == null) return 1;
        if (bv == null) return -1;
        if (av < bv) return sortDir === 'asc' ? -1 : 1;
        if (av > bv) return sortDir === 'asc' ? 1 : -1;
        return 0;
      });
  }, [vehicles, search, statusFilter, typeFilter, sortBy, sortDir]);

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setDialogOpen(true);
  };
  const openEdit = (v: Vehicle) => {
    setEditing(v);
    setForm({
      registration_number: v.registration_number,
      name_model: v.name_model,
      type: v.type,
      max_load_capacity: String(v.max_load_capacity),
      odometer: String(v.odometer),
      acquisition_cost: String(v.acquisition_cost),
      status: v.status,
      region: v.region ?? '',
    });
    setDialogOpen(true);
  };
  const submit = async () => {
    if (!form.registration_number.trim() || form.registration_number.trim().length < 3) {
      toast.error('Registration number must be at least 3 characters.');
      return;
    }
    if (!form.name_model.trim() || form.name_model.trim().length < 2) {
      toast.error('Name / Model must be at least 2 characters.');
      return;
    }
    const maxLoad = parseFloat(form.max_load_capacity as string);
    const odometer = parseFloat(form.odometer as string);
    const acqCost = parseFloat(form.acquisition_cost as string);
    if (isNaN(maxLoad) || maxLoad <= 0) {
      toast.error('Max load capacity must be greater than 0 kg.');
      return;
    }
    if (isNaN(odometer) || odometer < 0) {
      toast.error('Odometer reading cannot be negative.');
      return;
    }
    if (isNaN(acqCost) || acqCost <= 0) {
      toast.error('Acquisition cost must be greater than $0.');
      return;
    }
    if (!form.region?.trim() || form.region.trim().length < 2) {
      toast.error('Operational region must be at least 2 characters.');
      return;
    }
    const payload = {
      ...form,
      max_load_capacity: maxLoad,
      odometer: odometer,
      acquisition_cost: acqCost,
    };
    try {
      if (editing) {
        await updateVehicle(editing.id, payload);
        toast.success('Vehicle updated');
      } else {
        await createVehicle(payload);
        toast.success('Vehicle created');
      }
      setDialogOpen(false);
      load();
    } catch (e: any) {
      toast.error(e?.response?.data?.message ?? 'Failed to save vehicle');
    }
  };
  const confirmDelete = async () => {
    if (deleteId == null) return;
    try {
      await deleteVehicle(deleteId);
      toast.success('Vehicle deleted');
      load();
    } catch (e: any) {
      toast.error(e?.response?.data?.message ?? 'Failed to delete');
    } finally {
      setDeleteId(null);
    }
  };

  const sortHead = (key: keyof Vehicle, label: string) => (
    <TableHead
      className="cursor-pointer select-none whitespace-nowrap"
      onClick={() => {
        if (sortBy === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
        else {
          setSortBy(key);
          setSortDir('asc');
        }
      }}
    >
      {label}
      {sortBy === key && (sortDir === 'asc' ? ' ↑' : ' ↓')}
    </TableHead>
  );

  return (
    <AppShell>
      <PageHeader
        title="Vehicle Registry"
        description="Fleet master data, capacity, and lifecycle status."
        actions={
          canEdit ? (
            <Button onClick={openCreate} className="gap-2">
              <Plus className="h-4 w-4" /> Add Vehicle
            </Button>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <Lock className="h-3.5 w-3.5" /> Read-only for {role}
            </div>
          )
        }
      />

      <Card className="border-slate-200/70 dark:border-slate-800">
        <CardContent className="p-4 sm:p-6">
          <div className="mb-4 grid gap-2 sm:grid-cols-[1fr_auto_auto]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search registration, model, region..."
                className="pl-9"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full sm:w-[160px]">
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
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-full sm:w-[160px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {VEHICLE_TYPES.map((t) => (
                  <SelectItem key={t} value={t}>
                    {t}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-200/70 dark:border-slate-800">
            <Table>
              <TableHeader>
                <TableRow>
                  {sortHead('registration_number', 'Registration')}
                  {sortHead('name_model', 'Name / Model')}
                  {sortHead('type', 'Type')}
                  {sortHead('max_load_capacity', 'Max Load (kg)')}
                  {sortHead('odometer', 'Odometer (km)')}
                  {sortHead('acquisition_cost', 'Cost ($)')}
                  {sortHead('region', 'Region')}
                  {sortHead('status', 'Status')}
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} className="py-10 text-center text-sm text-slate-500">
                      No vehicles match your filters.
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.map((v) => (
                    <TableRow key={v.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-900/40">
                      <TableCell className="font-mono text-xs font-medium">
                        {v.registration_number}
                      </TableCell>
                      <TableCell className="font-medium">{v.name_model}</TableCell>
                      <TableCell>{v.type}</TableCell>
                      <TableCell>{v.max_load_capacity.toLocaleString()}</TableCell>
                      <TableCell>{v.odometer.toLocaleString()}</TableCell>
                      <TableCell>${v.acquisition_cost.toLocaleString()}</TableCell>
                      <TableCell>{v.region ?? '—'}</TableCell>
                      <TableCell>
                        <StatusBadge status={v.status} />
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button
                            size="icon"
                            variant="ghost"
                            disabled={!canEdit}
                            onClick={() => openEdit(v)}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            size="icon"
                            variant="ghost"
                            disabled={!canEdit}
                            onClick={() => setDeleteId(v.id)}
                          >
                            <Trash2 className="h-4 w-4 text-rose-500" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editing ? 'Edit Vehicle' : 'Add Vehicle'}</DialogTitle>
            <DialogDescription>
              Register a vehicle in your fleet master data.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Registration Number</Label>
              <Input
                value={form.registration_number}
                onChange={(e) =>
                  setForm((f) => ({ ...f, registration_number: e.target.value }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Name / Model</Label>
              <Input
                value={form.name_model}
                onChange={(e) => setForm((f) => ({ ...f, name_model: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Type</Label>
              <Select
                value={form.type}
                onValueChange={(v) => setForm((f) => ({ ...f, type: v }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {VEHICLE_TYPES.map((t) => (
                    <SelectItem key={t} value={t}>
                      {t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={form.status}
                onValueChange={(v) => setForm((f) => ({ ...f, status: v as Vehicle['status'] }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STATUSES.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Max Load Capacity (kg)</Label>
              <Input
                type="number"
                value={form.max_load_capacity}
                onChange={(e) =>
                  setForm((f) => ({ ...f, max_load_capacity: e.target.value }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Odometer (km)</Label>
              <Input
                type="number"
                value={form.odometer}
                onChange={(e) => setForm((f) => ({ ...f, odometer: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Acquisition Cost ($)</Label>
              <Input
                type="number"
                value={form.acquisition_cost}
                onChange={(e) =>
                  setForm((f) => ({ ...f, acquisition_cost: e.target.value }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Region</Label>
              <Input
                value={form.region ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, region: e.target.value }))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={submit}>{editing ? 'Save Changes' : 'Create Vehicle'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteId != null} onOpenChange={(o) => !o && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this vehicle?</AlertDialogTitle>
            <AlertDialogDescription>
              This cannot be undone. Associated trips and logs will retain their references.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </AppShell>
  );
}
