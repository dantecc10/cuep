import { create } from "zustand";
import { api } from "@/lib/api";

interface AuthUser {
  id: number;
  email: string;
  nombre: string;
  apellido_paterno: string;
  role: string;
  sede_id: number | null;
  es_tutor: boolean;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  setToken: (token: string | null) => void;
  fetchUser: () => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: typeof window !== "undefined" ? localStorage.getItem("cuep_token") : null,
  user: null,
  setToken: (token) => {
    if (token) localStorage.setItem("cuep_token", token);
    else localStorage.removeItem("cuep_token");
    set({ token });
    if (token) get().fetchUser();
    else set({ user: null });
  },
  fetchUser: async () => {
    const token = get().token || (typeof window !== "undefined" ? localStorage.getItem("cuep_token") : null);
    if (!token) return;
    try {
      const res = await api.get("/auth/me", { headers: { Authorization: `Bearer ${token}` } });
      set({ user: res.data });
    } catch {
      set({ user: null });
    }
  },
  logout: () => {
    localStorage.removeItem("cuep_token");
    set({ token: null, user: null });
  },
}));
