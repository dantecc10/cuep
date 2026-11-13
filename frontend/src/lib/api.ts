import axios, { isAxiosError, type InternalAxiosRequestConfig } from "axios";
import { toast } from "sonner";

const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL,
  timeout: 10000,
  withCredentials: true,
});

const refreshClient = axios.create({
  baseURL,
  timeout: 10000,
  withCredentials: true,
});

const AUTH_ENDPOINTS = ["/auth/login", "/auth/refresh", "/auth/logout", "/auth/2fa/verify", "/auth/register"];

let refreshPromise: Promise<string> | null = null;

function isAuthEndpoint(url?: string) {
  return Boolean(url && AUTH_ENDPOINTS.some((endpoint) => url.includes(endpoint)));
}

function clearStoredSession() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("cuep_token");
  window.dispatchEvent(new Event("cuep:session-expired"));
}

async function refreshAccessToken() {
  const res = await refreshClient.post<{ access_token: string }>("/auth/refresh", {});
  const token = res.data.access_token;
  localStorage.setItem("cuep_token", token);
  window.dispatchEvent(new CustomEvent("cuep:token-refreshed", { detail: token }));
  return token;
}

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("cuep_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error?.response?.status;
    const config = error?.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;

    if (status === 401 && config && !config._retry && !isAuthEndpoint(config.url)) {
      config._retry = true;
      try {
        refreshPromise = refreshPromise ?? refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
        const token = await refreshPromise;
        config.headers.Authorization = `Bearer ${token}`;
        return api(config);
      } catch {
        clearStoredSession();
        if (typeof window !== "undefined" && !["/login", "/verify-2fa"].includes(window.location.pathname)) {
          window.location.assign("/login?expired=1");
        }
        return Promise.reject(error);
      }
    }

    if (!error?.response) {
      toast.error("No se pudo conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.");
    } else if (isAxiosError(error) && status >= 500) {
      toast.error("El servidor no respondió correctamente. Inténtalo más tarde.");
    }
    return Promise.reject(error);
  },
);
