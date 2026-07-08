import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api";
import { useAuth } from "../auth";
import { usePoll } from "../hooks";
import { fmtDate, fmtDateTime, slaText, timeAgo } from "../lib";
import type { RequestDetail as RequestDetailT, Technician } from "../types";
import { Badge, Empty, Loading, Modal, PriorityBadge, StatusBadge, useToast } from "../ui";

type Action = { label: string; action: string; kind: "primary" | "ghost" | "danger" };

export default function RequestDetail() {
  const { reference } = useParams();
  const { user } = useAuth();
  const toast = useToast();
  const { data: req, loading, reload } = usePoll<RequestDetailT>(
    () => api.get(`/api/requests/${reference}/`),
    [reference],
    8000,
  );
  const [assignOpen, setAssignOpen] = useState(false);
  const [comment, setComment] = useState("");
  const [internal, setInternal] = useState(false);
  const [busy, setBusy] = useState(false);

  if (!user) return null;
  if (loading && !req) return <Loading />;
  if (!req) return <div className="card"><Empty>Request not found.</Empty></div>;

  const role = user.role;
  const isRequester = req.requester.id === user.id;
  const isAssignee = req.assignee?.id === user.id;
  const isDispatch = role === "dispatcher" || role === "manager";
  const isTechSide = isAssignee || role === "manager";

  const act = async (action: string) => {
    setBusy(true);
    try {
      await api.post(`/api/requests/${reference}/${action}/`);
      toast("Updated");
      reload();
    } catch (e) {
      toast(e instanceof Error ? e.message : "Action failed", true);
    } finally {
      setBusy(false);
    }
  };

  const actions: (Action | "assign")[] = [];
  if (isDispatch) {
    if (req.status === "submitted") actions.push({ label: "Receive", action: "receive", kind: "ghost" });
    if (req.is_open) actions.push("assign");
  }
  if (isTechSide) {
    if (req.status === "assigned") actions.push({ label: "Start work", action: "start", kind: "primary" });
    if (req.status === "in_progress") {
      actions.push({ label: "Put on hold", action: "hold", kind: "ghost" });
      actions.push({ label: "Mark complete", action: "complete", kind: "primary" });
    }
    if (req.status === "on_hold") actions.push({ label: "Resume", action: "resume", kind: "primary" });
  }
  if (isRequester) {
    if (req.status === "completed") actions.push({ label: "Confirm & close", action: "close", kind: "primary" });
    if (req.is_open && req.status !== "completed") actions.push({ label: "Cancel", action: "cancel", kind: "ghost" });
    if (req.status === "completed" || req.status === "closed") actions.push({ label: "Reopen", action: "reopen", kind: "ghost" });
  }

  const sla = slaText(req.sla_due_at, req.sla_breached, req.is_open);
  const backTo = role === "customer" ? "/app" : role === "technician" ? "/jobs" : "/dispatch";

  const submitComment = async () => {
    if (!comment.trim()) return;
    setBusy(true);
    try {
      await api.post(`/api/requests/${reference}/comments/`, { body: comment, is_internal: internal });
      setComment("");
      setInternal(false);
      reload();
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Link to={backTo} className="muted" style={{ fontSize: 13 }}>← Back</Link>
      <div className="page-head" style={{ marginTop: 8 }}>
        <div>
          <h1>{req.reference}</h1>
          <div className="sub">{req.title}</div>
        </div>
        <div className="row-wrap">
          <StatusBadge status={req.status} label={req.status_display} />
          <PriorityBadge priority={req.priority} label={req.priority_display} />
          {sla.text && <Badge tone={sla.tone}>{sla.text}</Badge>}
        </div>
      </div>

      {actions.length > 0 && (
        <div className="row-wrap" style={{ marginBottom: 16 }}>
          {actions.map((a, i) =>
            a === "assign" ? (
              <button key="assign" className="btn" disabled={busy} onClick={() => setAssignOpen(true)}>
                {req.assignee ? "Reassign" : "Assign technician"}
              </button>
            ) : (
              <button
                key={a.action + i}
                className={`btn ${a.kind === "ghost" ? "btn--ghost" : a.kind === "danger" ? "btn--danger" : ""}`}
                disabled={busy}
                onClick={() => act(a.action)}
              >
                {a.label}
              </button>
            ),
          )}
        </div>
      )}

      <div className="grid-3">
        <div className="stack">
          <div className="card">
            <div className="card-head"><h3>Description</h3></div>
            <p style={{ margin: 0, whiteSpace: "pre-wrap" }}>{req.description || <span className="muted">No details provided.</span>}</p>
          </div>

          <div className="card">
            <div className="card-head"><h3>Updates</h3></div>
            <div className="stack" style={{ gap: 10 }}>
              {req.worklogs.length === 0 && <p className="muted" style={{ margin: 0, fontSize: 13 }}>No updates yet.</p>}
              {req.worklogs.map((w) => (
                <div key={w.id} className="listrow" style={{ alignItems: "flex-start" }}>
                  <div>
                    <div style={{ fontSize: 14 }}>{w.body}</div>
                    <div className="muted" style={{ fontSize: 11.5, marginTop: 2 }}>
                      {w.author_name} · {timeAgo(w.created_at)} {w.is_internal && <Badge tone="muted">internal</Badge>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 12 }}>
              <textarea className="textarea" value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Add an update…" style={{ minHeight: 70 }} />
              <div className="row" style={{ marginTop: 8, justifyContent: "space-between" }}>
                {role !== "customer" ? (
                  <label className="row muted" style={{ fontSize: 12.5, gap: 6 }}>
                    <input type="checkbox" checked={internal} onChange={(e) => setInternal(e.target.checked)} /> Internal note
                  </label>
                ) : <span />}
                <button className="btn btn--sm" disabled={busy || !comment.trim()} onClick={submitComment}>Post update</button>
              </div>
            </div>
          </div>
        </div>

        <div className="stack">
          <div className="card">
            <div className="card-head"><h3>Details</h3></div>
            <dl style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "8px 14px", margin: 0, fontSize: 13.5 }}>
              <dt className="muted">Department</dt><dd style={{ margin: 0, fontWeight: 600 }}>{req.department.name}</dd>
              {req.category_name && (<><dt className="muted">Type</dt><dd style={{ margin: 0 }}>{req.category_name}</dd></>)}
              <dt className="muted">Property</dt><dd style={{ margin: 0 }}>{req.location_label || "—"}{req.community ? `, ${req.community}` : ""}</dd>
              <dt className="muted">Raised by</dt><dd style={{ margin: 0 }}>{req.requester.name}</dd>
              <dt className="muted">Technician</dt><dd style={{ margin: 0 }}>{req.assignee ? req.assignee.name : "Unassigned"}</dd>
              <dt className="muted">Raised</dt><dd style={{ margin: 0 }}>{fmtDate(req.created_at)}</dd>
              {req.sla_due_at && (<><dt className="muted">SLA due</dt><dd style={{ margin: 0 }}>{fmtDateTime(req.sla_due_at)}</dd></>)}
            </dl>
          </div>

          <div className="card">
            <div className="card-head"><h3>Timeline</h3></div>
            <div className="timeline">
              {req.events.map((e) => (
                <div key={e.id} className="tl-item">
                  <div className="tl-dot" />
                  <div>
                    <div>{e.verb_display}{e.to_value ? ` → ${e.to_value}` : ""}</div>
                    <div className="muted" style={{ fontSize: 11.5 }}>{e.actor || "system"} · {fmtDateTime(e.created_at)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {assignOpen && (
        <AssignModal
          reference={req.reference}
          onClose={() => setAssignOpen(false)}
          onAssigned={() => {
            setAssignOpen(false);
            toast("Technician assigned");
            reload();
          }}
        />
      )}
    </>
  );
}

function AssignModal({ reference, onClose, onAssigned }: { reference: string; onClose: () => void; onAssigned: () => void }) {
  const toast = useToast();
  const { data, loading } = usePoll<Technician[]>(() => api.get(`/api/requests/${reference}/eligible-technicians/`), [reference]);
  const [busy, setBusy] = useState(false);

  const assign = async (id: number) => {
    setBusy(true);
    try {
      await api.post(`/api/requests/${reference}/assign/`, { technician: id });
      onAssigned();
    } catch (e) {
      toast(e instanceof Error ? e.message : "Assignment failed", true);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title="Assign a technician" onClose={onClose} width={440}>
      <p className="muted" style={{ marginTop: 0, fontSize: 13 }}>
        Only technicians who hold this skill and are available are shown.
      </p>
      {loading ? (
        <Loading />
      ) : !data || data.length === 0 ? (
        <Empty icon="🧰">No available technician has this skill right now.</Empty>
      ) : (
        <div className="stack" style={{ gap: 8 }}>
          {data.map((t) => (
            <div key={t.id} className="listrow">
              <div>
                <b>{t.name}</b>
                <div className="muted" style={{ fontSize: 12 }}>{t.title || "Technician"}</div>
              </div>
              <button className="btn btn--sm" disabled={busy} onClick={() => assign(t.id)}>Assign</button>
            </div>
          ))}
        </div>
      )}
    </Modal>
  );
}
