import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { WidgetSpec } from "../types";

const PALETTE = ["#2563eb", "#16a34a", "#db2777", "#d97706", "#7c3aed", "#0891b2"];

// When encoding.series is present we pivot long rows into wide rows so each
// series becomes its own line/bar.
function pivot(spec: WidgetSpec) {
  const { x, y, series } = spec.encoding;
  if (!series || !x || !y) {
    return { data: spec.data, seriesKeys: [y as string] };
  }
  const byX = new Map<string, Record<string, unknown>>();
  const seriesKeys = new Set<string>();
  for (const row of spec.data) {
    const xv = String(row[x]);
    const sv = String(row[series]);
    seriesKeys.add(sv);
    const bucket = byX.get(xv) ?? { [x]: row[x] };
    bucket[sv] = row[y];
    byX.set(xv, bucket);
  }
  return { data: [...byX.values()], seriesKeys: [...seriesKeys] };
}

export function ChartWidget({ spec }: { spec: WidgetSpec }) {
  const { x } = spec.encoding;
  const { data, seriesKeys } = pivot(spec);

  if (!data.length) {
    return <div className="empty">No rows returned.</div>;
  }

  const common = (
    <>
      <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
      <XAxis dataKey={x ?? undefined} tick={{ fontSize: 12 }} />
      <YAxis tick={{ fontSize: 12 }} width={56} />
      <Tooltip />
      {seriesKeys.length > 1 && <Legend />}
    </>
  );

  return (
    <ResponsiveContainer width="100%" height={260}>
      {spec.type === "line" ? (
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
          {common}
          {seriesKeys.map((key, i) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={PALETTE[i % PALETTE.length]}
              dot={false}
              strokeWidth={2}
            />
          ))}
        </LineChart>
      ) : (
        <BarChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
          {common}
          {seriesKeys.map((key, i) => (
            <Bar key={key} dataKey={key} fill={PALETTE[i % PALETTE.length]} />
          ))}
        </BarChart>
      )}
    </ResponsiveContainer>
  );
}
