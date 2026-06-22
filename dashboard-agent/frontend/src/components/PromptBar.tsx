import { useState, type FormEvent } from "react";

const SUGGESTIONS = [
  "Show weekly revenue by region",
  "Top 10 customers by order volume",
  "Monthly active users",
  "Revenue by product category",
];

export function PromptBar({
  onSubmit,
  busy,
}: {
  onSubmit: (request: string) => void;
  busy: boolean;
}) {
  const [value, setValue] = useState("");

  function submit(e: FormEvent) {
    e.preventDefault();
    if (value.trim()) {
      onSubmit(value.trim());
      setValue("");
    }
  }

  return (
    <div className="prompt-bar">
      <form onSubmit={submit}>
        <input
          value={value}
          placeholder="Ask for a chart or metric…  e.g. show weekly revenue by region"
          onChange={(e) => setValue(e.target.value)}
          disabled={busy}
          autoFocus
        />
        <button type="submit" disabled={busy || !value.trim()}>
          {busy ? "Building…" : "Add widget"}
        </button>
      </form>
      <div className="suggestions">
        {SUGGESTIONS.map((s) => (
          <button key={s} className="chip" disabled={busy} onClick={() => onSubmit(s)}>
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
