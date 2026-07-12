import { Link, useLocation, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  Truck,
  Users,
  Route as RouteIcon,
  Wrench,
  Fuel,
  BarChart3,
  LogOut,
} from 'lucide-react';
import type { ReactNode } from 'react';
import { useAuthStore } from '@/store/authStore';
import { UserRole } from '@/lib/constants';
import { cn } from '@/lib/utils';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';

const nav = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/vehicles', label: 'Vehicles', icon: Truck },
  { to: '/drivers', label: 'Drivers', icon: Users },
  { to: '/trips', label: 'Trips', icon: RouteIcon },
  { to: '/maintenance', label: 'Maintenance', icon: Wrench },
  { to: '/fuel-expenses', label: 'Fuel & Expenses', icon: Fuel },
  { to: '/reports', label: 'Reports', icon: BarChart3 },
] as const;

const roles: UserRole[] = [
  UserRole.FLEET_MANAGER,
  UserRole.DRIVER,
  UserRole.SAFETY_OFFICER,
  UserRole.FINANCIAL_ANALYST,
];

export function AppShell({ children }: { children?: ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const setRole = useAuthStore((s) => s.setRole);
  const logout = useAuthStore((s) => s.logout);
  const location = useLocation();
  const pathname = location.pathname;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/40 text-slate-900 dark:from-slate-950 dark:via-slate-950 dark:to-indigo-950/20 dark:text-slate-100">
      <div className="flex min-h-screen">
        <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-200/70 bg-white/70 backdrop-blur-xl lg:flex dark:border-slate-800 dark:bg-slate-950/60">
          <div className="flex h-16 items-center gap-2 px-6">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-500/30">
              <Truck className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-bold tracking-tight">TransitOps</div>
              <div className="text-[10px] uppercase tracking-widest text-slate-500">
                Operations Platform
              </div>
            </div>
          </div>
          <nav className="flex-1 space-y-1 px-3 py-4">
            {nav.map((item) => {
              const active = (item.to as string) === '/' ? pathname === '/' : pathname.startsWith(item.to);
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  className={cn(
                    'group flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-all',
                    active
                      ? 'bg-gradient-to-r from-indigo-500/10 to-violet-500/5 text-indigo-700 shadow-sm dark:text-indigo-300'
                      : 'text-slate-600 hover:bg-slate-100/70 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/50 dark:hover:text-slate-100',
                  )}
                >
                  <item.icon
                    className={cn(
                       'h-4 w-4 transition-transform group-hover:scale-110',
                       active && 'text-indigo-600 dark:text-indigo-400',
                    )}
                  />
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="border-t border-slate-200/70 p-4 dark:border-slate-800">
            <div className="flex items-center gap-3">
              <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-xs font-semibold text-white">
                {user?.name?.split(' ').map((n) => n[0]).join('').slice(0, 2) ?? 'U'}
              </div>
              <div className="min-w-0">
                <div className="truncate text-sm font-semibold">{user?.name ?? 'Guest'}</div>
                <div className="truncate text-xs text-slate-500">{user?.email}</div>
              </div>
            </div>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b border-slate-200/70 bg-white/70 px-4 backdrop-blur-xl sm:px-6 dark:border-slate-800 dark:bg-slate-950/60">
            <div className="min-w-0">
              <div className="text-xs uppercase tracking-widest text-slate-500">TransitOps</div>
              <div className="truncate text-lg font-semibold tracking-tight">
                {nav.find((n) => ((n.to as string) === '/' ? pathname === '/' : pathname.startsWith(n.to)))?.label ??
                  'Overview'}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Select value={user?.role} onValueChange={(v) => setRole(v as UserRole)}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Role" />
                </SelectTrigger>
                <SelectContent>
                  {roles.map((r) => (
                    <SelectItem key={r} value={r}>
                      {r}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button variant="ghost" size="icon" onClick={logout} title="Sign out">
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </header>
          <main className="flex-1 p-4 sm:p-6 lg:p-8">
            <div className="mx-auto w-full max-w-7xl">
              {children || <Outlet />}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4 sm:flex sm:flex-wrap sm:justify-between">
      <div className="min-w-0">
        <h1 className="truncate text-2xl font-bold tracking-tight sm:text-3xl">{title}</h1>
        {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}

export default AppShell;