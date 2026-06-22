import type { WidgetSpec } from "../types";

export function DataTable({ spec }: { spec: WidgetSpec }) {
  const columns = spec.columns.map((c) => c.name);
  if (!spec.data.length) {
    return <div className="empty">No rows returned.</div>;
  }
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {spec.data.slice(0, 100).map((row, i) => (
            <tr key={i}>
              {columns.map((c) => (
                <td key={c}>{row[c] == null ? "—" : String(row[c])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
