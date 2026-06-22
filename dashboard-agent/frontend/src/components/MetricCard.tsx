import type { WidgetSpec } from "../types";
import { formatValue } from "../format";

export function MetricCard({ spec }: { spec: WidgetSpec }) {
  const row = spec.data[0] ?? {};
  const valueKey = spec.encoding.value ?? spec.columns[0]?.name;
  const value = valueKey ? row[valueKey] : undefined;

  return (
    <div className="metric">
      <div className="metric-value">
        {formatValue(value, spec.encoding.value_format)}
      </div>
      {spec.encoding.label && row[spec.encoding.label] != null && (
        <div className="metric-label">{String(row[spec.encoding.label])}</div>
      )}
    </div>
  );
}
