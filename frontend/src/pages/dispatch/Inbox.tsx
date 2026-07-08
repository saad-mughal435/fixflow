import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../api";
import { usePoll } from "../../hooks";
import { slaText } from "../../lib";
import type { Paginated, RequestItem } from "../../types";
import { Badge, Empty, Loading, PriorityBadge, StatusBadge } from "../../ui";

const FILTERS: [string, string][] = [
  ["unassigned", "Unassigned"],
  ["all", "All open"],
  ["in_progress", "In progress"],
  ["on_hold", "On hold"],
];

export default function DispatchInbox() {
  const [filter, setFilter] = useState("unassigned");
  const navigate = useNavigate();
  const query = filter === "unassigned" ? "?unassigned=true" : filter === "all" ? "" : `?status=${filter}`;
  const { data, loading } = usePoll<Paginated<RequestItem>>(
    () => api.get(`/api/requests/${query}`),
    [filter],
    10000,
  );

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Department inbox</h1>
          <div className="sub">Incoming requests for your departments. Open one to assign a technician.</div>
        </div>
      </div>

      <div className="chips" style={{ marginBottom: 16 }}>
        {FILTERS.map(([v, label]) => (
          <button key={v} className={`chip ${filter === v ? "active" : ""}`} onClick={() => setFilter(v)}>
            {label}
          </button>
        ))}
      </div>

      {loading && !data ? (
        <Loading />
      ) : !data || data.results.length === 0 ? (
        <div className="card"><Empty icon="📭">Nothing here — inbox is clear.</Empty></div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Reference</th>
                  <th>Property</th>
                  <th>Department</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>SLA</th>
                  <th>Technician</th>
                </tr>
              </thead>
              <tbody>
                {data.results.map((r) => {
                  const sla = slaText(r.sla_due_at, r.sla_breached, r.is_open);
                  return (
                    <tr key={r.id} className="clickable" onClick={() => navigate(`/requests/${r.reference}`)}>
                      <td><b>{r.reference}</b><div className="muted" style={{ fontSize: 12 }}>{r.title}</div></td>
                      <td>{r.location_label || "—"}<div className="muted" style={{ fontSize: 12 }}>{r.community}</div></td>
                      <td>{r.department.name}</td>
                      <td><PriorityBadge priority={r.priority} label={r.priority_display} /></td>
                      <td><StatusBadge status={r.status} label={r.status_display} /></td>
                      <td>{sla.text ? <Badge tone={sla.tone}>{sla.text}</Badge> : <span className="muted">—</span>}</td>
                      <td>{r.assignee ? r.assignee.name : <Badge tone="warn">Unassigned</Badge>}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
