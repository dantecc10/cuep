import { create } from "zustand";

interface AuthState {
  token: string | null;
  setToken: (token: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: typeof window !== "undefined" ? localStorage.getItem("cuep_token") : null,
  setToken: (token) => {
    if (token) localStorage.setItem("cuep_token", token);
    else localStorage.removeItem("cuep_token");
    set({ token });
  },
  logout: () => {
    localStorage.removeItem("cuep_token");
    set({ token: null });
  },
}));
