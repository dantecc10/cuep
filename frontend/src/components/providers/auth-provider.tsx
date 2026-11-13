"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/store/auth";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const fetchUser = useAuthStore((s) => s.fetchUser);
  const setInitialized = useAuthStore((s) => s.setInitialized);
  const token = useAuthStore((s) => s.token);

  useEffect(() => {
    let cancelled = false;
    if (!token) {
      setInitialized(true);
      return;
    }
    fetchUser().finally(() => {
      if (!cancelled) setInitialized(true);
    });
    return () => {
      cancelled = true;
    };
  }, [token, fetchUser, setInitialized]);

  return <>{children}</>;
}
