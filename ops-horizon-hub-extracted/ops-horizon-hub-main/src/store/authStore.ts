import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Role, User } from '@/types';

interface AuthState {
  user: User | null;
  token: string | null;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  setRole: (role: Role) => void;
  logout: () => void;
}

const demoUser: User = {
  id: 1,
  name: 'Alex Morgan',
  email: 'alex@transitops.io',
  role: 'Fleet Manager',
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: demoUser,
      token: null,
      setUser: (user) => set({ user }),
      setToken: (token) => set({ token }),
      setRole: (role) => {
        const u = get().user ?? demoUser;
        set({ user: { ...u, role } });
      },
      logout: () => set({ user: null, token: null }),
    }),
    { name: 'auth-storage' },
  ),
);

export const roleCan = {
  manageFleet: (role?: Role) => role === 'Fleet Manager',
  manageMaintenance: (role?: Role) => role === 'Fleet Manager' || role === 'Safety Officer',
  manageFinance: (role?: Role) => role === 'Fleet Manager' || role === 'Financial Analyst',
  createTrips: (role?: Role) => role === 'Fleet Manager',
  completeTrips: (role?: Role) => role === 'Fleet Manager' || role === 'Driver',
};
