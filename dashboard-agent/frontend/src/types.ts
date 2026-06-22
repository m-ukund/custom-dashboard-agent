// Mirrors the backend's WidgetSpec (models.py). This is the standardized,
// dynamic contract the agent emits and the GUI renders.

export type WidgetType = "metric" | "line" | "bar" | "table";

export interface ColumnMeta {
  name: string;
  dtype: string;
}

export interface Encoding {
  x?: string | null;
  y?: string | null;
  series?: string | null;
  value?: string | null;
  label?: string | null;
  value_format?: "currency" | "number" | "percent" | null;
}

export interface WidgetSpec {
  id: string;
  title: string;
  request: string;
  type: WidgetType;
  sql: string;
  columns: ColumnMeta[];
  data: Record<string, unknown>[];
  encoding: Encoding;
  notes?: string | null;
}

export interface WidgetSuccess {
  widget: WidgetSpec;
  request_id: string;
  attempts: number;
  latency_ms: number;
}

export interface ApiError {
  error: string;
  detail: string;
  stage: string;
  request_id: string;
  clarification?: string | null;
}
