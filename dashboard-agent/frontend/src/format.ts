import type { Encoding } from "./types";

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});
const number = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const percent = new Intl.NumberFormat("en-US", {
  style: "percent",
  maximumFractionDigits: 1,
});

export function formatValue(value: unknown, fmt?: Encoding["value_format"]): string {
  if (value === null || value === undefined) return "—";
  const num = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(num)) return String(value);
  switch (fmt) {
    case "currency":
      return currency.format(num);
    case "percent":
      return percent.format(num);
    case "number":
      return number.format(num);
    default:
      return typeof value === "number" ? number.format(num) : String(value);
  }
}
