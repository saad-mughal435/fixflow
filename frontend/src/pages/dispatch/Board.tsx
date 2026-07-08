import { useNavigate } from "react-router-dom";

import { api } from "../../api";
import { usePoll } from "../../hooks";
import { slaText } from "../../lib";
import type { Paginated, RequestItem } from "../../types";
import { Badge, Loading, PriorityBadge } from "../../ui";

const COLUMNS: { label: string; statuses: string[] }[] = [
  { label: "New", statuses: ["submitted", "received"] },
  { label: "Assigned", statuses: ["assigned"] },
  { label: "In progress", statuses: ["in_progress"] },
  { label: "On hold", statuses: ["on_hold"] },
  { label: "Completed", statuses: ["completed", "closed"] },
];

export default function DispatchBoard() {
  const navigate = useNavigate();
  const { data, loading } = usePoll<Paginated<RequestItem>>(
    () => api.get("/api/requests/?ordering=-created_at"),
    [],
    12000,
  );

  if (loading && !data) return <Loading />;
  const rows = data?.results || [];

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Status board</h1>
          <div className="sub">Your departments’ requests, by stage. Showing the most recent {rows.length}.</div>
        </div>
      </div>

      <div style={{ display: "flex", gap: 12, overflowX: "auto", paddingBottom: 8 }}>
        {COLUMNS.map((col) => {
          const items = rows.filter((r) => col.statuses.includes(r.status));
          return (
            <div key={col.label} style={{ flex: "0 0 260px", background: "var(--bg-2)", border: "1px solid var(--line)", borderRadius: 12, padding: 10 }}>
              <div className="row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
                <b style={{ fontSize: 12.5, textTransform: "uppercase", letterSpacing: ".03em", color: "var(--ink-2)" }}>{col.label}</b>
                <span className="badge badge--muted">{items.length}</span>
              </div>
              {items.map((r) => {
                const sla = slaText(r.sla_due_at, r.sla_breached, r.is_open);
                return (
                  <div
                    key={r.id}
                    className="card"
                    style={{ padding: 11, marginBottom: 8, cursor: "pointer", borderLeft: `3px solid ${sla.tone === "urgent" ? "var(--urgent)" : sla.tone === "warn" ? "var(--warn)" : "var(--line-2)"}` }}
                    onClick={() => navigate(`/requests/${r.reference}`)}
                  >
                    <div style={{ fontSize: 13.5, fontWeight: 600 }}>{r.title}</div>
                    <div className="muted" style={{ fontSize: 11.5, margin: "3px 0 6px" }}>{r.reference} · {r.department.name}</div>
                    <div className="row-wrap" style={{ gap: 6 }}>
                      <PriorityBadge priority={r.priority} label={r.priority_display} />
                      {sla.text && <Badge tone={sla.tone}>{sla.text}</Badge>}
                    </div>
                    {r.assignee && <div className="muted" style={{ fontSize: 11.5, marginTop: 6 }}>👷 {r.assignee.name}</div>}
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </>
  );
}
