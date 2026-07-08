import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../api";
import { usePoll } from "../../hooks";
import { fmtDate, slaText } from "../../lib";
import type { Paginated, RequestItem } from "../../types";
import { Badge, Empty, Loading, PriorityBadge, StatusBadge } from "../../ui";

const FILTERS: [string, string][] = [
  ["", "All"],
  ["submitted", "Submitted"],
  ["in_progress", "In progress"],
  ["completed", "Completed"],
  ["closed", "Closed"],
];

export default function CustomerRequests() {
  const [status, setStatus] = useState("");
  const navigate = useNavigate();
  const { data, loading } = usePoll<Paginated<RequestItem>>(
    () => api.get(`/api/requests/${status ? `?status=${status}` : ""}`),
    [status],
    10000,
  );

  return (
    <>
      <div className="page-head">
        <div>
          <h1>My requests</h1>
          <div className="sub">Track your maintenance requests in real time.</div>
        </div>
        <button className="btn" onClick={() => navigate("/app/new")}>+ New request</button>
      </div>

      <div className="chips" style={{ marginBottom: 16 }}>
        {FILTERS.map(([v, label]) => (
          <button key={v} className={`chip ${status === v ? "active" : ""}`} onClick={() => setStatus(v)}>
            {label}
          </button>
        ))}
      </div>

      {loading && !data ? (
        <Loading />
      ) : !data || data.results.length === 0 ? (
        <div className="card">
          <Empty icon="🧰">No requests yet. Tap “New request” to raise one.</Empty>
        </div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Reference</th>
                  <th>Department</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Technician</th>
                  <th>SLA</th>
                </tr>
              </thead>
              <tbody>
                {data.results.map((r) => {
                  const sla = slaText(r.sla_due_at, r.sla_breached, r.is_open);
                  return (
                    <tr key={r.id} className="clickable" onClick={() => navigate(`/requests/${r.reference}`)}>
                      <td>
                        <b>{r.reference}</b>
                        <div className="muted" style={{ fontSize: 12 }}>{r.title}</div>
                      </td>
                      <td>{r.department.name}</td>
                      <td><PriorityBadge priority={r.priority} label={r.priority_display} /></td>
                      <td><StatusBadge status={r.status} label={r.status_display} /></td>
                      <td>{r.assignee ? r.assignee.name : <span className="muted">—</span>}</td>
                      <td>{sla.text ? <Badge tone={sla.tone}>{sla.text}</Badge> : <span className="muted">{fmtDate(r.created_at)}</span>}</td>
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
