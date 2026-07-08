import { useNavigate } from "react-router-dom";

import { api } from "../../api";
import { usePoll } from "../../hooks";
import { slaText } from "../../lib";
import type { Paginated, RequestItem } from "../../types";
import { Badge, Empty, Loading, PriorityBadge, StatusBadge } from "../../ui";

const ACTIVE = ["assigned", "in_progress", "on_hold"];

export default function TechJobs() {
  const navigate = useNavigate();
  const { data, loading } = usePoll<Paginated<RequestItem>>(
    () => api.get("/api/requests/?ordering=sla_due_at"),
    [],
    10000,
  );

  if (loading && !data) return <Loading />;
  const rows = data?.results || [];
  const active = rows.filter((r) => ACTIVE.includes(r.status));
  const done = rows.filter((r) => ["completed", "closed"].includes(r.status));

  const Card = ({ r }: { r: RequestItem }) => {
    const sla = slaText(r.sla_due_at, r.sla_breached, r.is_open);
    return (
      <div
        className="card"
        style={{ padding: 14, cursor: "pointer", borderLeft: `3px solid ${sla.tone === "urgent" ? "var(--urgent)" : sla.tone === "warn" ? "var(--warn)" : "var(--line-2)"}` }}
        onClick={() => navigate(`/requests/${r.reference}`)}
      >
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div style={{ fontSize: 14.5, fontWeight: 600 }}>{r.title}</div>
          <StatusBadge status={r.status} label={r.status_display} />
        </div>
        <div className="muted" style={{ fontSize: 12, margin: "4px 0 8px" }}>
          {r.reference} · {r.department.name} · {r.location_label || "—"}{r.community ? `, ${r.community}` : ""}
        </div>
        <div className="row-wrap" style={{ gap: 6 }}>
          <PriorityBadge priority={r.priority} label={r.priority_display} />
          {sla.text && <Badge tone={sla.tone}>{sla.text}</Badge>}
        </div>
      </div>
    );
  };

  return (
    <>
      <div className="page-head">
        <div>
          <h1>My jobs</h1>
          <div className="sub">Your assigned work, most urgent first.</div>
        </div>
      </div>

      <h3 style={{ fontSize: 14, marginBottom: 10 }}>Active ({active.length})</h3>
      {active.length === 0 ? (
        <div className="card"><Empty icon="✅">No active jobs right now.</Empty></div>
      ) : (
        <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", marginBottom: 24 }}>
          {active.map((r) => <Card key={r.id} r={r} />)}
        </div>
      )}

      {done.length > 0 && (
        <>
          <h3 style={{ fontSize: 14, margin: "8px 0 10px" }}>Recently completed</h3>
          <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
            {done.map((r) => <Card key={r.id} r={r} />)}
          </div>
        </>
      )}
    </>
  );
}
