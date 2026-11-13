"use client";

import { create } from "zustand";
import { isAxiosError } from "axios";
import { api } from "@/lib/api";

export interface AuthUser {
  id: number;
  email: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno?: string | null;
  role: string;
  sede_id: number | null;
  es_tutor: boolean;
  foto_url?: string | null;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  initialized: boolean;
  setToken: (token: string | null) => void;
  setInitialized: (initialized: boolean) => void;
  updateUser: (patch: Partial<AuthUser>) => void;
  fetchUser: () => Promise<void>;
  logout: () => void;
}

function storedToken() {
  return typeof window !== "undefined" ? localStorage.getItem("cuep_token") : null;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: storedToken(),
  user: null,
  initialized: false,
  setToken: (token) => {
    if (typeof window !== "undefined") {
      if (token) localStorage.setItem("cuep_token", token);
      else localStorage.removeItem("cuep_token");
    }
    set({ token });
    if (!token) set({ user: null, initialized: true });
  },
  setInitialized: (initialized) => set({ initialized }),
  updateUser: (patch) => {
    const current = get().user;
    if (current) set({ user: { ...current, ...patch } });
  },
  fetchUser: async () => {
    const token = get().token || storedToken();
    if (!token) {
      set({ user: null, initialized: true });
      return;
    }
    try {
      const res = await api.get<AuthUser>("/auth/me");
      if (get().token) set({ user: res.data, initialized: true });
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 401) {
        if (typeof window !== "undefined") localStorage.removeItem("cuep_token");
        set({ token: null, user: null, initialized: true });
      } else {
        set({ initialized: true });
      }
    }
  },
  logout: () => {
    void api.post("/auth/logout").catch(() => undefined);
    if (typeof window !== "undefined") localStorage.removeItem("cuep_token");
    set({ token: null, user: null, initialized: true });
  },
}));

if (typeof window !== "undefined") {
  window.addEventListener("cuep:token-refreshed", (event) => {
    const token = (event as CustomEvent<string>).detail;
    useAuthStore.setState({ token });
  });
  window.addEventListener("cuep:session-expired", () => {
    useAuthStore.setState({ token: null, user: null, initialized: true });
  });
}
