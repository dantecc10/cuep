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
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return <div className="py-8 text-center text-sm text-muted-foreground">{emptyMessage}</div>;
  }

  return (
    <div className="rounded-card border border-primary overflow-hidden bg-surface">
      <table className="w-full text-sm">
        <thead className="bg-paper/60">
          <tr>
            {columns.map((col) => (
              <th key={col.key} className={`px-4 py-3 text-left font-semibold text-primary ${col.className || ""}`}>{col.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={keyExtractor(item)} className="border-t border-primary/10 hover:bg-paper/30">
              {columns.map((col) => (
                <td key={col.key} className={`px-4 py-3 ${col.className || ""}`}>
                  {col.render ? col.render(item) : String((item as Record<string, unknown>)[col.key] ?? "-")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
