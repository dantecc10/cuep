"use client";
import { useEffect } from "react";
import { useAuthStore } from "@/store/auth";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const fetchUser = useAuthStore((s) => s.fetchUser);
  const token = useAuthStore((s) => s.token);
  useEffect(() => {
    if (token) fetchUser();
  }, [token, fetchUser]);
  return <>{children}</>;
}
