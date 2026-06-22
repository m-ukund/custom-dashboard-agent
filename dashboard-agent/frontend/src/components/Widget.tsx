import type { WidgetSpec } from "../types";
import { ChartWidget } from "./ChartWidget";
import { DataTable } from "./DataTable";
import { MetricCard } from "./MetricCard";
import { useState, type FormEvent } from "react";

// Generic dispatcher: one envelope (WidgetSpec) -> the right renderer. Adding a
// new widget type means adding one case here and one branch in the agent.
export function Widget({
  spec,
  attempts,
  latencyMs,
  onRefine,
  onRemove,
  busy,
}: {
  spec: WidgetSpec;
  attempts?: number;
  latencyMs?: number;
  onRefine: (instruction: string) => void;
  onRemove: () => void;
  busy: boolean;
}) {
  const [showSql, setShowSql] = useState(false);
  const [refine, setRefine] = useState("");

  function submitRefine(e: FormEvent) {
    e.preventDefault();
    if (refine.trim()) {
      onRefine(refine.trim());
      setRefine("");
    }
  }

  return (
    <div className="widget">
      <div className="widget-head">
        <h3>{spec.title}</h3>
        <button className="icon-btn" onClick={onRemove} title="Remove">
          ✕
        </button>
      </div>

      <div className="widget-body">
        {spec.type === "metric" && <MetricCard spec={spec} />}
        {(spec.type === "line" || spec.type === "bar") && <ChartWidget spec={spec} />}
        {spec.type === "table" && <DataTable spec={spec} />}
      </div>

      {spec.notes && <p className="widget-notes">{spec.notes}</p>}

      <form className="refine" onSubmit={submitRefine}>
        <input
          value={refine}
          placeholder="Refine (e.g. break this down by category)…"
          onChange={(e) => setRefine(e.target.value)}
          disabled={busy}
        />
        <button type="submit" disabled={busy}>
          {busy ? "…" : "Update"}
        </button>
      </form>

      <div className="widget-foot">
        <button className="link" onClick={() => setShowSql((s) => !s)}>
          {showSql ? "hide SQL" : "view SQL"}
        </button>
        {attempts != null && (
          <span className="muted">
            {attempts} attempt{attempts === 1 ? "" : "s"}
            {latencyMs != null ? ` · ${Math.round(latencyMs)} ms` : ""}
          </span>
        )}
      </div>
      {showSql && <pre className="sql">{spec.sql}</pre>}
    </div>
  );
}
