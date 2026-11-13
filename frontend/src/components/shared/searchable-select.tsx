"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Check, ChevronDown, Search } from "lucide-react";

export interface SearchableOption {
  value: string;
  label: string;
  description?: string;
}

export function SearchableSelect({
  value,
  onChange,
  options,
  placeholder = "Selecciona una opción",
  searchPlaceholder = "Buscar...",
  emptyLabel = "Sin opciones",
  clearLabel,
  disabled = false,
  className = "",
  id,
}: {
  value: string;
  onChange: (value: string) => void;
  options: SearchableOption[];
  placeholder?: string;
  searchPlaceholder?: string;
  emptyLabel?: string;
  clearLabel?: string;
  disabled?: boolean;
  className?: string;
  id?: string;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  const selected = options.find((option) => option.value === value);
  const filtered = useMemo(() => {
    const term = query.trim().toLocaleLowerCase("es");
    if (!term) return options;
    return options.filter((option) => {
      const text = [option.label, option.description, option.value]
        .filter(Boolean)
        .join(" ")
        .toLocaleLowerCase("es");
      return text.includes(term);
    });
  }, [options, query]);

  useEffect(() => {
    function handlePointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
        setQuery("");
      }
    }
    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, []);

  useEffect(() => {
    if (!open) setQuery("");
  }, [open]);

  function select(nextValue: string) {
    onChange(nextValue);
    setOpen(false);
    setQuery("");
  }

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <button
        type="button"
        id={id}
        disabled={disabled}
        onClick={() => setOpen((current) => !current)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className="flex h-10 w-full items-center justify-between gap-2 border border-ink/30 bg-surface px-3 text-left text-sm text-ink outline-none transition focus-visible:border-primary disabled:cursor-not-allowed disabled:opacity-60"
      >
        <span className={selected ? "text-ink" : "text-ink/45"}>
          {selected?.label || placeholder}
        </span>
        <ChevronDown aria-hidden="true" className="h-4 w-4 shrink-0 text-ink/40" />
      </button>

      {open && (
        <div className="absolute z-20 mt-1 w-full border border-ink bg-surface shadow-[4px_4px_0_#171313]">
          <div className="border-b border-ink/10 p-2">
            <label className="relative block">
              <Search
                aria-hidden="true"
                className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink/40"
              />
              <input
                autoFocus
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Escape") setOpen(false);
                }}
                placeholder={searchPlaceholder}
                className="h-8 w-full border border-ink/20 bg-paper/40 pl-8 pr-2 text-xs text-ink outline-none focus-visible:border-primary"
              />
            </label>
          </div>
          <ul role="listbox" className="max-h-56 overflow-y-auto py-1">
            {clearLabel && (
              <li>
                <button
                  type="button"
                  onClick={() => select("")}
                  className="flex w-full items-center justify-between px-3 py-2 text-left text-xs text-ink/60 transition hover:bg-accent/10"
                >
                  {clearLabel}
                  {!value && <Check aria-hidden="true" className="h-3.5 w-3.5 text-primary" />}
                </button>
              </li>
            )}
            {filtered.length === 0 ? (
              <li className="px-3 py-3 text-xs text-ink/50">{emptyLabel}</li>
            ) : (
              filtered.map((option) => {
                const isSelected = option.value === value;
                return (
                  <li key={option.value}>
                    <button
                      type="button"
                      role="option"
                      aria-selected={isSelected}
                      onClick={() => select(option.value)}
                      className={`flex w-full items-start justify-between gap-2 px-3 py-2 text-left transition ${
                        isSelected ? "bg-primary/5 text-ink" : "text-ink/75 hover:bg-accent/10"
                      }`}
                    >
                      <span>
                        <span className="block text-xs font-semibold">{option.label}</span>
                        {option.description && (
                          <span className="mt-0.5 block font-mono text-[0.56rem] uppercase tracking-[0.06em] text-ink/45">
                            {option.description}
                          </span>
                        )}
                      </span>
                      {isSelected && <Check aria-hidden="true" className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />}
                    </button>
                  </li>
                );
              })
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
