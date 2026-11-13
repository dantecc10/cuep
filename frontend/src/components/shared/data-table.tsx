"use client";

import { useMemo, useState } from "react";
import { ArrowDown, ArrowUp, ArrowUpDown, Search, SlidersHorizontal, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

export interface TableFilterOption {
  value: string;
  label: string;
}

export interface TableFilter<T> {
  key: string;
  label: string;
  options: TableFilterOption[];
  getValue: (item: T) => string | null | undefined;
}

export interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => React.ReactNode;
  className?: string;
  sortValue?: (item: T) => string | number | null | undefined;
  sortable?: boolean;
  searchValue?: (item: T) => string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[] | undefined;
  isLoading: boolean;
  keyExtractor: (item: T) => string | number;
  emptyMessage?: string;
  searchable?: boolean;
  searchPlaceholder?: string;
  getSearchText?: (item: T) => string;
  filters?: TableFilter<T>[];
  initialSort?: { key: string; direction: "asc" | "desc" };
  toolbarActions?: React.ReactNode;
}

const collator = new Intl.Collator("es", { numeric: true, sensitivity: "base" });

function defaultSortValue<T>(item: T, key: string): string | number {
  const value = (item as Record<string, unknown>)[key];
  if (typeof value === "number") return value;
  if (value === null || value === undefined) return "";
  return String(value);
}

function defaultSearchText<T>(item: T, columns: Column<T>[]): string {
  return columns
    .filter((column) => column.key !== "acciones")
    .map((column) => {
      if (column.searchValue) return column.searchValue(item);
      return String(defaultSortValue(item, column.key));
    })
    .join(" ");
}

export function DataTable<T>({
  columns,
  data,
  isLoading,
  keyExtractor,
  emptyMessage = "No hay registros",
  searchable = true,
  searchPlaceholder = "Buscar...",
  getSearchText,
  filters = [],
  initialSort,
  toolbarActions,
}: DataTableProps<T>) {
  const [search, setSearch] = useState("");
  const [filterValues, setFilterValues] = useState<Record<string, string>>({});
  const [sort, setSort] = useState<{ key: string; direction: "asc" | "desc" } | null>(
    initialSort ?? null,
  );

  const rows = useMemo(() => data || [], [data]);
  const hasControls = searchable || filters.length > 0 || Boolean(toolbarActions);
  const activeFilterCount = Object.values(filterValues).filter(Boolean).length;
  const hasActiveControls = search.trim().length > 0 || activeFilterCount > 0;

  const processed = useMemo(() => {
    let result = [...rows];

    if (searchable && search.trim()) {
      const term = search.trim().toLocaleLowerCase("es");
      result = result.filter((item) => {
        const text = getSearchText ? getSearchText(item) : defaultSearchText(item, columns);
        return text.toLocaleLowerCase("es").includes(term);
      });
    }

    for (const filter of filters) {
      const selected = filterValues[filter.key];
      if (!selected) continue;
      result = result.filter((item) => {
        const value = filter.getValue(item);
        return value !== null && value !== undefined && String(value) === selected;
      });
    }

    if (sort) {
      const column = columns.find((item) => item.key === sort.key);
      const direction = sort.direction === "asc" ? 1 : -1;
      result.sort((a, b) => {
        const aValue = column?.sortValue
          ? column.sortValue(a)
          : defaultSortValue(a, sort.key);
        const bValue = column?.sortValue
          ? column.sortValue(b)
          : defaultSortValue(b, sort.key);
        if (aValue === null || aValue === undefined) return 1;
        if (bValue === null || bValue === undefined) return -1;
        if (typeof aValue === "number" && typeof bValue === "number") {
          return (aValue - bValue) * direction;
        }
        return collator.compare(String(aValue), String(bValue)) * direction;
      });
    }

    return result;
  }, [rows, searchable, search, getSearchText, columns, filters, filterValues, sort]);

  function toggleSort(column: Column<T>) {
    const sortableColumn = column.sortable ?? Boolean(column.sortValue);
    if (!sortableColumn) return;
    setSort((current) => {
      if (current?.key !== column.key) {
        return { key: column.key, direction: "asc" };
      }
      return {
        key: column.key,
        direction: current.direction === "asc" ? "desc" : "asc",
      };
    });
  }

  function clearControls() {
    setSearch("");
    setFilterValues({});
  }

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-11 w-full" />
        <Skeleton className="h-11 w-full" />
        <Skeleton className="h-11 w-full" />
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div className="border border-dashed border-ink/25 bg-surface px-4 py-10 text-center font-editorial text-base text-ink/55">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {hasControls && (
        <div className="poster-card flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-1 flex-wrap items-center gap-2">
            {searchable && (
              <label className="relative min-w-[220px] flex-1">
                <Search
                  aria-hidden="true"
                  className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink/40"
                />
                <Input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder={searchPlaceholder}
                  className="h-10 w-full pl-9"
                  aria-label={searchPlaceholder}
                />
              </label>
            )}
            {filters.map((filter) => (
              <label key={filter.key} className="flex items-center gap-2">
                <span className="sr-only">{filter.label}</span>
                <SlidersHorizontal aria-hidden="true" className="h-4 w-4 text-ink/40" />
                <select
                  aria-label={filter.label}
                  className="h-10 border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                  value={filterValues[filter.key] || ""}
                  onChange={(event) =>
                    setFilterValues((current) => ({
                      ...current,
                      [filter.key]: event.target.value,
                    }))
                  }
                >
                  <option value="">{filter.label}: todos</option>
                  {filter.options.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            ))}
            {hasActiveControls && (
              <button
                type="button"
                onClick={clearControls}
                className="inline-flex h-10 items-center gap-1 border border-ink/20 px-3 font-mono text-[0.62rem] font-bold uppercase tracking-[0.08em] text-ink/60 transition hover:border-ink hover:text-ink"
              >
                <X aria-hidden="true" className="h-3.5 w-3.5" />
                Limpiar
              </button>
            )}
          </div>
          <div className="flex items-center gap-3">
            {toolbarActions}
            <span className="whitespace-nowrap font-mono text-[0.62rem] uppercase tracking-[0.08em] text-ink/45">
              {processed.length} de {rows.length}
            </span>
          </div>
        </div>
      )}

      {processed.length === 0 ? (
        <div className="border border-dashed border-ink/25 bg-surface px-4 py-10 text-center">
          <p className="font-editorial text-base text-ink/55">Sin resultados con los filtros actuales.</p>
          <button
            type="button"
            onClick={clearControls}
            className="link-arrow mt-3 text-primary"
          >
            Limpiar búsqueda y filtros
          </button>
        </div>
      ) : (
        <div className="poster-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-sm">
              <thead className="border-b border-ink bg-paper/70">
                <tr>
                  {columns.map((col) => {
                    const sortableColumn = col.sortable ?? Boolean(col.sortValue);
                    const isSorted = sort?.key === col.key;
                    return (
                      <th
                        key={col.key}
                        aria-sort={
                          isSorted
                            ? sort?.direction === "asc"
                              ? "ascending"
                              : "descending"
                            : "none"
                        }
                        className={`px-4 py-3 text-left font-mono text-[0.62rem] font-bold uppercase tracking-[0.1em] text-ink ${col.className || ""}`}
                      >
                        {sortableColumn ? (
                          <button
                            type="button"
                            onClick={() => toggleSort(col)}
                            className="inline-flex items-center gap-1.5 text-left transition hover:text-primary"
                          >
                            {col.header}
                            {isSorted ? (
                              sort?.direction === "asc" ? (
                                <ArrowUp aria-hidden="true" className="h-3 w-3" />
                              ) : (
                                <ArrowDown aria-hidden="true" className="h-3 w-3" />
                              )
                            ) : (
                              <ArrowUpDown aria-hidden="true" className="h-3 w-3 text-ink/30" />
                            )}
                          </button>
                        ) : (
                          col.header
                        )}
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody>
                {processed.map((item) => (
                  <tr
                    key={keyExtractor(item)}
                    className="border-t border-ink/10 transition hover:bg-accent/10"
                  >
                    {columns.map((col) => (
                      <td
                        key={col.key}
                        className={`px-4 py-3 align-middle text-ink/80 ${col.className || ""}`}
                      >
                        {col.render
                          ? col.render(item)
                          : String((item as Record<string, unknown>)[col.key] ?? "-")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
