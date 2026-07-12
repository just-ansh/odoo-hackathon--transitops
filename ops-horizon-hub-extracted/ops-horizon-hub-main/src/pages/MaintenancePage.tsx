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
import { StatusBadge } from '@/components/StatusBadge';
import {
  closeMaintenanceLog,
  getMaintenanceLogs,
  getVehicles,
  openMaintenanceLog,
} from '@/lib/api';
import type { MaintenanceLog, Vehicle } from '@/types';
import { roleCan, useAuthStore } from '@/store/authStore';
import { Lock, Plus, Wrench } from 'lucide-react';
import { toast } from 'sonner';

export default function MaintenancePage() {
  const role = useAuthStore((s) => s.user?.role);
  const canEdit = roleCan.manageMaintenance(role);

  const [logs, setLogs] = useState<MaintenanceLog[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [closeState, setCloseState] = useState<MaintenanceLog | null>(null);
  const [form, setForm] = useState({ vehicle_id: null as number | null, description: '' });
  const [closeCost, setCloseCost] = useState(0);

  const load = () => {
    Promise.all([getMaintenanceLogs(), getVehicles()])
      .then(([l, v]: any) => {
        setLogs(Array.isArray(l) ? l : l?.data ?? []);
        setVehicles(Array.isArray(v) ? v : v?.data ?? []);
      })
      .catch(() => {});
  };
  useEffect(() => {
    load();
  }, []);

  const vehiclesById = useMemo(() => new Map(vehicles.map((v) => [v.id, v])), [vehicles]);
  const eligibleVehicles = vehicles.filter((v) => v.status !== 'In Shop' && v.status !== 'Retired');

  const open = logs.filter((l) => l.status === 'Open');
  const history = logs.filter((l) => l.status === 'Closed');

  const submitOpen = async () => {
    if (!form.vehicle_id || !form.description.trim()) {
      toast.error('Select a vehicle and describe the problem.');
      return;
    }
    try {
      await openMaintenanceLog({ vehicle_id: form.vehicle_id, description: form.description });
      toast.success('Maintenance opened — vehicle moved to In Shop');
      setOpenDialog(false);
      setForm({ vehicle_id: null, description: '' });
      load();
    } catch (e: any) {
      toast.error(e?.response?.data?.message ?? 'Failed to open log');
    }
  };

  const submitClose = async () => {
    if (!closeState) return;
    if (closeCost < 0) {
      toast.error('Cost cannot be negative.');
      return;
    }
    try {
      await closeMaintenanceLog(closeState.id, closeCost);
      toast.success('Maintenance closed — vehicle restored to Available');
      setCloseState(null);
      setCloseCost(0);
      load();
    } catch (e: any) {
      toast.error(e?.response?.data?.message ?? 'Failed to close log');
    }
  };

  const renderTable = (items: MaintenanceLog[], variant: 'open' | 'history') => (
    <div className="overflow-x-auto rounded-lg border border-slate-200/70 dark:border-slate-800">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Vehicle</TableHead>
            <TableHead>Description</TableHead>
            <TableHead>Logged</TableHead>
            {variant === 'history' && <TableHead>Closed</TableHead>}
            <TableHead>Cost</TableHead>
            <TableHead>Status</TableHead>
            {variant === 'open' && <TableHead className="text-right">Actions</TableHead>}
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={variant === 'open' ? 6 : 6}
                className="py-10 text-center text-sm text-slate-500"
              >
                No {variant === 'open' ? 'open' : 'closed'} maintenance logs.
              </TableCell>
            </TableRow>
          ) : (
            items.map((l) => {
              const v = vehiclesById.get(l.vehicle_id);
              return (
                <TableRow key={l.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-900/40">
                  <TableCell className="font-medium">
                    {v ? `${v.registration_number} — ${v.name_model}` : `#${l.vehicle_id}`}
                  </TableCell>
                  <TableCell className="max-w-md text-sm text-slate-600 dark:text-slate-300">
                    {l.description}
                  </TableCell>
                  <TableCell className="text-xs text-slate-500">
                    {new Date(l.logged_at).toLocaleString()}
                  </TableCell>
                  {variant === 'history' && (
                    <TableCell className="text-xs text-slate-500">
                      {l.closed_at ? new Date(l.closed_at).toLocaleString() : '—'}
                    </TableCell>
                  )}
                  <TableCell>${(l.cost ?? 0).toLocaleString()}</TableCell>
                  <TableCell>
                    <StatusBadge status={l.status} />
                  </TableCell>
                  {variant === 'open' && (
                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        disabled={!canEdit}
                        onClick={() => {
                          setCloseState(l);
                          setCloseCost(0);
                        }}
                      >
                        <Wrench className="mr-1 h-3.5 w-3.5" /> Close
                      </Button>
                    </TableCell>
                  )}
                </TableRow>
              );
            })
          )}
        </TableBody>
      </Table>
    </div>
  );

  return (
    <AppShell>
      <PageHeader
        title="Maintenance"
        description="Track vehicle repairs. Opening a log moves the vehicle to In Shop."
        actions={
          canEdit ? (
            <Button onClick={() => setOpenDialog(true)} className="gap-2">
              <Plus className="h-4 w-4" /> New Log
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
          <Tabs defaultValue="open">
            <TabsList>
              <TabsTrigger value="open">Open ({open.length})</TabsTrigger>
              <TabsTrigger value="history">History ({history.length})</TabsTrigger>
            </TabsList>
            <TabsContent value="open" className="mt-4">
              {renderTable(open, 'open')}
            </TabsContent>
            <TabsContent value="history" className="mt-4">
              {renderTable(history, 'history')}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <Dialog open={openDialog} onOpenChange={setOpenDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Open Maintenance Log</DialogTitle>
            <DialogDescription>
              The selected vehicle will be moved to In Shop and hidden from dispatch.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Vehicle</Label>
              <Select
                value={form.vehicle_id?.toString() ?? ''}
                onValueChange={(v) => setForm((f) => ({ ...f, vehicle_id: Number(v) }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select vehicle" />
                </SelectTrigger>
                <SelectContent>
                  {eligibleVehicles.length === 0 ? (
                    <div className="px-2 py-1.5 text-xs text-slate-500">No eligible vehicles</div>
                  ) : (
                    eligibleVehicles.map((v) => (
                      <SelectItem key={v.id} value={v.id.toString()}>
                        {v.registration_number} — {v.name_model} ({v.status})
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Problem Description</Label>
              <Textarea
                rows={4}
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                placeholder="Describe the issue, symptoms, or scheduled service..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setOpenDialog(false)}>
              Cancel
            </Button>
            <Button onClick={submitOpen}>Open Log</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={closeState != null} onOpenChange={(o) => !o && setCloseState(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Close Maintenance</DialogTitle>
            <DialogDescription>
              Record the final repair cost. The vehicle will be restored to Available.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label>Repair Cost ($)</Label>
            <Input
              type="number"
              value={closeCost}
              onChange={(e) => setCloseCost(Number(e.target.value))}
            />
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setCloseState(null)}>
              Cancel
            </Button>
            <Button onClick={submitClose}>Close Log</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppShell>
  );
}
