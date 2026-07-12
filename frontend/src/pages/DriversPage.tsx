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
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { createDriver, deleteDriver, getDrivers, updateDriver } from '@/lib/api';
import type { Driver } from '@/types';
import { roleCan, useAuthStore } from '@/store/authStore';
import { AlertTriangle, Plus, Pencil, Trash2, Search, Lock } from 'lucide-react';
import { toast } from 'sonner';

const STATUSES: Driver['status'][] = ['Available', 'On Trip', 'Off Duty', 'Suspended'];
const CATEGORIES = ['A', 'B', 'C', 'D', 'CDL-A', 'CDL-B'];

type FormState = {
  name: string;
  license_number: string;
  license_category: string;
  license_expiry_date: string;
  contact_number: string;
  safety_score: string;
  status: Driver['status'];
};
const emptyForm: FormState = {
  name: '',
  license_number: '',
  license_category: 'B',
  license_expiry_date: new Date().toISOString().slice(0, 10),
  contact_number: '',
  safety_score: '80',
  status: 'Available',
};

const isExpired = (d: string) => new Date(d) < new Date();
const isExpiringSoon = (d: string) => {
  const days = (new Date(d).getTime() - Date.now()) / 86400000;
  return days >= 0 && days <= 30;
};

export default function DriversPage() {
  const role = useAuthStore((s) => s.user?.role);
  const canEdit = roleCan.manageFleet(role);

  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [editing, setEditing] = useState<Driver | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const load = () =>
    getDrivers()
      .then((d: any) => setDrivers(Array.isArray(d) ? d : d?.data ?? []))
      .catch(() => setDrivers([]));
  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => {
    const s = search.toLowerCase();
    return drivers.filter(
      (d) =>
        (statusFilter === 'all' || d.status === statusFilter) &&
        (!s ||
          d.name.toLowerCase().includes(s) ||
          d.license_number.toLowerCase().includes(s) ||
          d.contact_number.toLowerCase().includes(s)),
    );
  }, [drivers, search, statusFilter]);

  const alerts = useMemo(() => {
    const expired = drivers.filter((d) => isExpired(d.license_expiry_date));
    const lowScore = drivers.filter((d) => d.safety_score < 60);
    return { expired, lowScore };
  }, [drivers]);

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setDialogOpen(true);
  };
  const openEdit = (d: Driver) => {
    setEditing(d);
    setForm({
      name: d.name,
      license_number: d.license_number,
      license_category: d.license_category,
      license_expiry_date: d.license_expiry_date,
      contact_number: d.contact_number,
      safety_score: String(d.safety_score),
      status: d.status,
    });
    setDialogOpen(true);
  };
  const submit = async () => {
    if (!form.name.trim() || form.name.trim().length < 2) {
      toast.error('Name must be at least 2 characters.');
      return;
    }
    if (!form.contact_number.trim() || form.contact_number.trim().length < 5) {
      toast.error('A valid contact number is required.');
      return;
    }
    if (!form.license_number.trim() || form.license_number.trim().length < 3) {
      toast.error('License number must be at least 3 characters.');
      return;
    }
    if (!form.license_expiry_date) {
      toast.error('License expiry date is required.');
      return;
    }
    const safetyScore = parseFloat(form.safety_score as string);
    if (isNaN(safetyScore) || safetyScore < 0 || safetyScore > 100) {
      toast.error('Safety score must be between 0 and 100.');
      return;
    }
    const payload = { ...form, safety_score: safetyScore };
    try {
      if (editing) {
        await updateDriver(editing.id, payload);
        toast.success('Driver updated');
      } else {
        await createDriver(payload);
        toast.success('Driver created');
      }
      setDialogOpen(false);
      load();
    } catch (e: any) {
      toast.error(e?.response?.data?.message ?? 'Failed to save');
    }
  };
  const confirmDelete = async () => {
    if (deleteId == null) return;
    try {
      await deleteDriver(deleteId);
      toast.success('Driver deleted');
      load();
    } catch (e: any) {
      toast.error(e?.response?.data?.message ?? 'Failed to delete');
    } finally {
      setDeleteId(null);
    }
  };

  return (
    <AppShell>
      <PageHeader
        title="Driver Registry"
        description="License validity, safety performance, and duty status."
        actions={
          canEdit ? (
            <Button onClick={openCreate} className="gap-2">
              <Plus className="h-4 w-4" /> Add Driver
            </Button>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <Lock className="h-3.5 w-3.5" /> Read-only for {role}
            </div>
          )
        }
      />

      {(alerts.expired.length > 0 || alerts.lowScore.length > 0) && (
        <div className="mb-4 grid gap-3 sm:grid-cols-2">
          {alerts.expired.length > 0 && (
            <Alert className="border-rose-200 bg-rose-50 dark:border-rose-900/50 dark:bg-rose-950/30">
              <AlertTriangle className="h-4 w-4 text-rose-600" />
              <AlertTitle className="text-rose-700 dark:text-rose-300">
                {alerts.expired.length} expired license
                {alerts.expired.length > 1 ? 's' : ''}
              </AlertTitle>
              <AlertDescription className="text-rose-600/80 dark:text-rose-300/80">
                {alerts.expired
                  .slice(0, 3)
                  .map((d) => d.name)
                  .join(', ')}
                {alerts.expired.length > 3 && ` +${alerts.expired.length - 3} more`}
              </AlertDescription>
            </Alert>
          )}
          {alerts.lowScore.length > 0 && (
            <Alert className="border-amber-200 bg-amber-50 dark:border-amber-900/50 dark:bg-amber-950/30">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              <AlertTitle className="text-amber-700 dark:text-amber-300">
                {alerts.lowScore.length} low safety score
                {alerts.lowScore.length > 1 ? 's' : ''}
              </AlertTitle>
              <AlertDescription className="text-amber-600/80 dark:text-amber-300/80">
                Drivers scoring below 60 need review.
              </AlertDescription>
            </Alert>
          )}
        </div>
      )}

      <Card className="border-slate-200/70 dark:border-slate-800">
        <CardContent className="p-4 sm:p-6">
          <div className="mb-4 grid gap-2 sm:grid-cols-[1fr_auto]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search name, license, phone..."
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
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-200/70 dark:border-slate-800">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>License #</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Expiry</TableHead>
                  <TableHead>Contact</TableHead>
                  <TableHead>Safety</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="py-10 text-center text-sm text-slate-500">
                      No drivers found.
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.map((d) => {
                    const expired = isExpired(d.license_expiry_date);
                    const soon = !expired && isExpiringSoon(d.license_expiry_date);
                    const lowScore = d.safety_score < 60;
                    return (
                      <TableRow
                        key={d.id}
                        className="hover:bg-slate-50/60 dark:hover:bg-slate-900/40"
                      >
                        <TableCell className="font-medium">{d.name}</TableCell>
                        <TableCell className="font-mono text-xs">{d.license_number}</TableCell>
                        <TableCell>{d.license_category}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span
                              className={
                                expired
                                  ? 'text-rose-600 font-semibold'
                                  : soon
                                    ? 'text-amber-600 font-semibold'
                                    : ''
                              }
                            >
                              {new Date(d.license_expiry_date).toLocaleDateString()}
                            </span>
                            {expired && (
                              <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-semibold text-rose-700 dark:bg-rose-500/20 dark:text-rose-300">
                                EXPIRED
                              </span>
                            )}
                            {soon && (
                              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-700 dark:bg-amber-500/20 dark:text-amber-300">
                                SOON
                              </span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>{d.contact_number}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                              <div
                                className={`h-full rounded-full ${
                                  lowScore
                                    ? 'bg-rose-500'
                                    : d.safety_score < 80
                                      ? 'bg-amber-500'
                                      : 'bg-emerald-500'
                                }`}
                                style={{ width: `${Math.min(100, d.safety_score)}%` }}
                              />
                            </div>
                            <span className={lowScore ? 'font-semibold text-rose-600' : ''}>
                              {d.safety_score}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <StatusBadge status={d.status} />
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            <Button
                              size="icon"
                              variant="ghost"
                              disabled={!canEdit}
                              onClick={() => openEdit(d)}
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                            <Button
                              size="icon"
                              variant="ghost"
                              disabled={!canEdit}
                              onClick={() => setDeleteId(d.id)}
                            >
                              <Trash2 className="h-4 w-4 text-rose-500" />
                            </Button>
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

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editing ? 'Edit Driver' : 'Add Driver'}</DialogTitle>
            <DialogDescription>Driver profile and credentials.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Name</Label>
              <Input
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Contact Number</Label>
              <Input
                value={form.contact_number}
                onChange={(e) => setForm((f) => ({ ...f, contact_number: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>License Number</Label>
              <Input
                value={form.license_number}
                onChange={(e) => setForm((f) => ({ ...f, license_number: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>License Category</Label>
              <Select
                value={form.license_category}
                onValueChange={(v) => setForm((f) => ({ ...f, license_category: v }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>License Expiry Date</Label>
              <Input
                type="date"
                value={form.license_expiry_date}
                onChange={(e) => setForm((f) => ({ ...f, license_expiry_date: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Safety Score (0-100)</Label>
              <Input
                type="number"
                min={0}
                max={100}
                value={form.safety_score}
                onChange={(e) => setForm((f) => ({ ...f, safety_score: e.target.value }))}
              />
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label>Status</Label>
              <Select
                value={form.status}
                onValueChange={(v) => setForm((f) => ({ ...f, status: v as Driver['status'] }))}
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
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={submit}>{editing ? 'Save Changes' : 'Create Driver'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteId != null} onOpenChange={(o) => !o && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this driver?</AlertDialogTitle>
            <AlertDialogDescription>This action cannot be undone.</AlertDialogDescription>
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
