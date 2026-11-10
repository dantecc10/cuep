"use client";

import { useRef, useState } from "react";
import axios from "axios";
import { ImagePlus } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface FotoUploaderProps {
  value?: string | null;
  onChange: (url: string) => void;
  label?: string;
  id?: string;
}

export function FotoUploader({ value, onChange, label = "Fotografía", id = "foto" }: FotoUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [showUrl, setShowUrl] = useState(false);
  const [error, setError] = useState("");

  async function handleFile(file: File | undefined) {
    if (!file) return;
    setUploading(true);
    setError("");
    const data = new FormData();
    data.append("file", file);
    try {
      const res = await api.post<{ url: string }>("/uploads/avatar", data);
      onChange(res.data.url);
      setShowUrl(false);
    } catch (err) {
      const status = axios.isAxiosError(err) ? err.response?.status : undefined;
      if (status === 503) {
        setShowUrl(true);
        setError("R2 no está configurado. Puedes pegar una URL pública para tu foto.");
      } else if (status === 413) {
        setError("La imagen no debe superar 5 MB.");
      } else {
        setError("No pudimos subir la imagen. Intenta de nuevo o usa una URL pública.");
      }
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div className="space-y-3">
      <Label htmlFor={id}>{label}</Label>
      <div className="flex flex-wrap items-center gap-4">
        {value ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={value} alt="Vista previa de la fotografía" className="h-20 w-20 border border-ink/20 object-cover" />
        ) : (
          <div className="grid h-20 w-20 place-items-center border border-dashed border-ink/30 bg-sand text-ink/35">
            <ImagePlus className="h-6 w-6" aria-hidden="true" />
          </div>
        )}
        <div className="flex flex-wrap gap-2">
          <input
            ref={inputRef}
            id={id}
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            className="sr-only"
            onChange={(event) => handleFile(event.target.files?.[0])}
          />
          <Button type="button" variant="outline" size="sm" onClick={() => inputRef.current?.click()} disabled={uploading}>
            {uploading ? "Subiendo..." : "Subir foto"}
          </Button>
          <Button type="button" variant="ghost" size="sm" onClick={() => setShowUrl((current) => !current)}>
            Usar URL
          </Button>
        </div>
      </div>
      {showUrl && (
        <Input
          value={value || ""}
          onChange={(event) => onChange(event.target.value)}
          placeholder="https://ejemplo.com/mi-foto.jpg"
          aria-label="URL pública de la fotografía"
        />
      )}
      {error && <p className="text-xs font-semibold text-primary">{error}</p>}
    </div>
  );
}
