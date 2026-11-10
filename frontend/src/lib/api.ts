import axios from "axios";
import { toast } from "sonner";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("cuep_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    if (!error?.response) {
      toast.error("No se pudo conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.");
    } else if (status >= 500) {
      toast.error("El servidor no respondió correctamente. Inténtalo más tarde.");
    }
    return Promise.reject(error);
  },
);
