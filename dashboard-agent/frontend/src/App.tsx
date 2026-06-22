import { useEffect, useState } from "react";
import { createWidget, fetchSchema, RequestError, type SchemaTable } from "./api";
import { PromptBar } from "./components/PromptBar";
import { Widget } from "./components/Widget";
import { ErrorCard } from "./components/ErrorCard";
import type { ApiError, WidgetSuccess } from "./types";

interface WidgetCard {
  result: WidgetSuccess;
}

export default function App() {
  const [widgets, setWidgets] = useState<WidgetCard[]>([]);
  const [error, setError] = useState<ApiError | null>(null);
  const [busyGlobal, setBusyGlobal] = useState(false);
  const [busyWidget, setBusyWidget] = useState<string | null>(null);
  const [schema, setSchema] = useState<SchemaTable[]>([]);

  useEffect(() => {
    fetchSchema().then(setSchema).catch(() => setSchema([]));
  }, []);

  async function addWidget(request: string) {
    setBusyGlobal(true);
    setError(null);
    try {
      const result = await createWidget(request);
      setWidgets((w) => [...w, { result }]);
    } catch (e) {
      if (e instanceof RequestError) setError(e.payload);
      else setError({ error: "network_error", detail: String(e), stage: "client", request_id: "-" });
    } finally {
      setBusyGlobal(false);
    }
  }

  async function refineWidget(id: string, instruction: string) {
    const card = widgets.find((w) => w.result.widget.id === id);
    if (!card) return;
    setBusyWidget(id);
    setError(null);
    try {
      const result = await createWidget(instruction, card.result.widget);
      setWidgets((ws) =>
        ws.map((w) => (w.result.widget.id === id ? { result } : w)),
      );
    } catch (e) {
      if (e instanceof RequestError) setError(e.payload);
      else setError({ error: "network_error", detail: String(e), stage: "client", request_id: "-" });
    } finally {
      setBusyWidget(null);
    }
  }

  function removeWidget(id: string) {
    setWidgets((ws) => ws.filter((w) => w.result.widget.id !== id));
  }

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>Custom Dashboard Agent</h1>
          <p className="subtitle">
            Ask in plain English. Every query runs read-only and is validated before it renders.
          </p>
        </div>
        <SchemaPill schema={schema} />
      </header>

      <PromptBar onSubmit={addWidget} busy={busyGlobal} />

      {error && <ErrorCard error={error} onDismiss={() => setError(null)} />}

      {widgets.length === 0 && !busyGlobal && (
        <div className="placeholder">
          <p>No widgets yet. Add one above to start building your dashboard.</p>
        </div>
      )}

      <div className="grid">
        {widgets.map(({ result }) => (
          <Widget
            key={result.widget.id}
            spec={result.widget}
            attempts={result.attempts}
            latencyMs={result.latency_ms}
            busy={busyWidget === result.widget.id}
            onRefine={(instruction) => refineWidget(result.widget.id, instruction)}
            onRemove={() => removeWidget(result.widget.id)}
          />
        ))}
        {busyGlobal && <div className="widget skeleton">Building widget…</div>}
      </div>
    </div>
  );
}

function SchemaPill({ schema }: { schema: SchemaTable[] }) {
  if (!schema.length) return <span className="schema-pill muted">schema: not connected</span>;
  return (
    <span className="schema-pill" title={schema.map((t) => t.name).join(", ")}>
      {schema.length} tables connected
    </span>
  );
}
