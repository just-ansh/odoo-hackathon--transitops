import { create } from "zustand";
import { persist } from "zustand/middleware";
import { UserRole } from "@/lib/constants";

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
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: "transitops-auth" }
  )
);