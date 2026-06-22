import type { ApiError } from "../types";

// Failures are first-class UI, not a console error. A clarification (from the
// triage stage) is rendered as a prompt-to-the-user rather than a hard error.
export function ErrorCard({ error, onDismiss }: { error: ApiError; onDismiss: () => void }) {
  const isClarification = Boolean(error.clarification);
  return (
    <div className={`error-card ${isClarification ? "clarify" : ""}`}>
      <div className="error-head">
        <strong>{isClarification ? "Need a bit more detail" : "Couldn't build that widget"}</strong>
        <button className="icon-btn" onClick={onDismiss}>
          ✕
        </button>
      </div>
      {isClarification ? (
        <p>{error.clarification}</p>
      ) : (
        <p>{error.detail}</p>
      )}
      <div className="error-meta muted">
        stage: {error.stage} · {error.error} · request {error.request_id}
      </div>
    </div>
  );
}
