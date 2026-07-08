import { api } from "../../api";
import { usePoll } from "../../hooks";
import type { Metrics } from "../../types";
import { KPI, Loading } from "../../ui";

export default function ManageDashboard() {
  const { data, loading } = usePoll<Metrics>(() => api.get("/api/metrics/dashboard/"), [], 30000);

  if (loading && !data) return <Loading />;
  if (!data) return null;

  const maxDept = Math.max(1, ...data.by_department.map((d) => d.count));
  const maxVol = Math.max(1, ...data.volume_14d.map((v) => v.count));

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Operations dashboard</h1>
          <div className="sub">Live portfolio overview across all departments.</div>
        </div>
      </div>

      <div className="kpis" style={{ marginBottom: 18 }}>
        <KPI label="Open requests" value={data.open} tone="info" />
        <KPI label="Unassigned" value={data.unassigned} tone={data.unassigned ? "warn" : "ok"} />
        <KPI label="SLA breached" value={data.sla_breached} tone={data.sla_breached ? "urgent" : "ok"} />
        <KPI label="Total (all time)" value={data.total} />
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-head"><h3>Open by department</h3></div>
          {data.by_department.length === 0 ? (
            <p className="muted" style={{ margin: 0 }}>Nothing open.</p>
          ) : (
            <div className="stack" style={{ gap: 10 }}>
              {data.by_department.map((d) => (
                <div key={d.department} className="row" style={{ gap: 12 }}>
                  <span style={{ width: 130, fontSize: 13, color: "var(--ink-2)" }}>{d.department}</span>
                  <span className="bar-track" style={{ flex: 1 }}>
                    <span className="bar-fill" style={{ width: `${(d.count / maxDept) * 100}%` }} />
                  </span>
                  <b style={{ width: 24, textAlign: "right", fontSize: 13 }}>{d.count}</b>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-head"><h3>By status</h3></div>
          <div className="stack" style={{ gap: 8 }}>
            {data.by_status.map((s) => (
              <div key={s.status} className="row" style={{ justifyContent: "space-between" }}>
                <span style={{ fontSize: 13, textTransform: "capitalize" }}>{s.status.replace("_", " ")}</span>
                <b style={{ fontSize: 13 }}>{s.count}</b>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid-2" style={{ marginTop: 14 }}>
        <div className="card">
          <div className="card-head"><h3>New requests · 14 days</h3></div>
          <div className="row" style={{ alignItems: "flex-end", gap: 4, height: 90 }}>
            {data.volume_14d.map((v) => (
              <div key={v.date} title={`${v.date}: ${v.count}`} style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-end", height: "100%" }}>
                <div style={{ background: "var(--teal)", borderRadius: "4px 4px 0 0", height: `${(v.count / maxVol) * 100}%`, minHeight: v.count ? 4 : 0 }} />
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-head"><h3>Technician workload (open)</h3></div>
          {data.technician_workload.length === 0 ? (
            <p className="muted" style={{ margin: 0 }}>No active assignments.</p>
          ) : (
            <div className="stack" style={{ gap: 8 }}>
              {data.technician_workload.map((t) => (
                <div key={t.technician} className="row" style={{ justifyContent: "space-between" }}>
                  <span style={{ fontSize: 13 }}>{t.technician}</span>
                  <span className="badge badge--muted">{t.open} open</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
