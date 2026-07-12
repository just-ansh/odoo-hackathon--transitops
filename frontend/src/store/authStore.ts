import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserRole } from '@/lib/constants';

interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
}

interface AuthState {
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  setRole: (role: UserRole) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      setRole: (role) => {
        const u = get().user;
        if (u) {
          set({ user: { ...u, role } });
        }
      },
      logout: () => set({ token: null, user: null }),
    }),
    { name: "transitops-auth" }
  )
);

export const roleCan = {
  manageFleet: (role?: UserRole) => role === 'Fleet Manager',
  manageMaintenance: (role?: UserRole) => role === 'Fleet Manager' || role === 'Safety Officer',
  manageFinance: (role?: UserRole) => role === 'Fleet Manager' || role === 'Financial Analyst',
  createTrips: (role?: UserRole) => role === 'Fleet Manager' || role === 'Driver',
  completeTrips: (role?: UserRole) => role === 'Fleet Manager' || role === 'Driver',
};