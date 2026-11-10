import { Skeleton } from "@/components/ui/skeleton";

export interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[] | undefined;
  isLoading: boolean;
  keyExtractor: (item: T) => string | number;
  emptyMessage?: string;
}

export function DataTable<T>({ columns, data, isLoading, keyExtractor, emptyMessage = "No hay registros" }: DataTableProps<T>) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-11 w-full" />
        <Skeleton className="h-11 w-full" />
        <Skeleton className="h-11 w-full" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return <div className="border border-dashed border-ink/25 bg-surface px-4 py-10 text-center font-editorial text-base text-ink/55">{emptyMessage}</div>;
  }

  return (
    <div className="poster-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead className="border-b border-ink bg-paper/70">
            <tr>
              {columns.map((col) => (
                <th key={col.key} className={`px-4 py-3 text-left font-mono text-[0.62rem] font-bold uppercase tracking-[0.1em] text-ink ${col.className || ""}`}>
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((item) => (
              <tr key={keyExtractor(item)} className="border-t border-ink/10 transition hover:bg-yellow/15">
                {columns.map((col) => (
                  <td key={col.key} className={`px-4 py-3 align-middle text-ink/80 ${col.className || ""}`}>
                    {col.render ? col.render(item) : String((item as Record<string, unknown>)[col.key] ?? "-")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
