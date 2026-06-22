import type { ApiError, WidgetSpec, WidgetSuccess } from "./types";

const BASE = "/api";

export class RequestError extends Error {
  constructor(public payload: ApiError) {
    super(payload.detail);
  }
}

export async function createWidget(
  request: string,
  previousWidget?: WidgetSpec | null,
): Promise<WidgetSuccess> {
  const res = await fetch(`${BASE}/widgets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      request,
      previous_widget: previousWidget ?? null,
    }),
  });

  const body = await res.json();
  if (!res.ok) {
    throw new RequestError(body as ApiError);
  }
  return body as WidgetSuccess;
}

export interface SchemaTable {
  name: string;
  columns: ColumnInfo[];
  foreign_keys: string[];
}
export interface ColumnInfo {
  name: string;
  dtype: string;
}

export async function fetchSchema(): Promise<SchemaTable[]> {
  const res = await fetch(`${BASE}/schema`);
  if (!res.ok) return [];
  const body = await res.json();
  return body.tables as SchemaTable[];
}
