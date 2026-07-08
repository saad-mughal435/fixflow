export type Tone = "ok" | "info" | "warn" | "urgent" | "muted";

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export function fmtDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-GB", {
    day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
  });
}

export function timeAgo(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (d < 0) {
    const a = Math.abs(d);
    if (a < 3600) return `in ${Math.floor(a / 60)}m`;
    if (a < 86400) return `in ${Math.floor(a / 3600)}h`;
    return `in ${Math.floor(a / 86400)}d`;
  }
  if (d < 60) return "just now";
  if (d < 3600) return `${Math.floor(d / 60)}m ago`;
  if (d < 86400) return `${Math.floor(d / 3600)}h ago`;
  return `${Math.floor(d / 86400)}d ago`;
}

const STATUS_TONE: Record<string, Tone> = {
  submitted: "info", received: "info", assigned: "info",
  in_progress: "warn", on_hold: "muted",
  completed: "ok", closed: "muted", cancelled: "muted",
};
export function statusTone(status: string): Tone {
  return STATUS_TONE[status] || "muted";
}

const PRIORITY_TONE: Record<string, Tone> = {
  p1_emergency: "urgent", p2_urgent: "warn", p3_routine: "info", p4_low: "muted",
};
export function priorityTone(priority: string): Tone {
  return PRIORITY_TONE[priority] || "muted";
}

export function slaText(dueAt: string | null, breached: boolean, isOpen: boolean): { text: string; tone: Tone } {
  if (!dueAt || !isOpen) return { text: "", tone: "muted" };
  const mins = Math.round((new Date(dueAt).getTime() - Date.now()) / 60000);
  if (breached || mins <= 0) {
    const over = mins < 0 ? -mins : 0;
    return { text: over ? `${humanMins(over)} overdue` : "SLA breached", tone: "urgent" };
  }
  return { text: `${humanMins(mins)} left`, tone: mins < 120 ? "warn" : "ok" };
}

function humanMins(mins: number): string {
  if (mins < 60) return `${mins}m`;
  if (mins < 1440) return `${Math.floor(mins / 60)}h`;
  return `${Math.floor(mins / 1440)}d`;
}
