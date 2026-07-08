import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import type { ReactNode } from "react";

import { api } from "./api";
import { useAuth } from "./auth";
import { timeAgo } from "./lib";
import type { AppNotification, Role } from "./types";
import { Modal } from "./ui";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || "http://127.0.0.1:8000";

type NavItem = { to: string; label: string; ic: string; end?: boolean };

const NAV: Record<Role, NavItem[]> = {
  customer: [
    { to: "/app", label: "My requests", ic: "🏠", end: true },
    { to: "/app/new", label: "New request", ic: "➕" },
  ],
  dispatcher: [
    { to: "/dispatch", label: "Inbox", ic: "📥", end: true },
    { to: "/dispatch/board", label: "Board", ic: "🗂️" },
  ],
  technician: [{ to: "/jobs", label: "My jobs", ic: "🔧", end: true }],
  manager: [
    { to: "/manage", label: "Dashboard", ic: "📊", end: true },
    { to: "/dispatch", label: "Inbox", ic: "📥" },
    { to: "/dispatch/board", label: "Board", ic: "🗂️" },
  ],
  anonymous: [],
};

function Bell() {
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<AppNotification[]>([]);

  const refresh = () =>
    api.get<{ unread: number }>("/api/notifications/unread-count/").then((d) => setUnread(d.unread)).catch(() => {});

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 30000);
    return () => clearInterval(t);
  }, []);

  const openList = async () => {
    setOpen(true);
    try {
      setItems(await api.get<AppNotification[]>("/api/notifications/"));
    } catch {
      /* ignore */
    }
  };
  const markAll = async () => {
    await api.post("/api/notifications/mark-all-read/");
    setOpen(false);
    refresh();
  };

  return (
    <>
      <button className="icon-btn" onClick={openList} aria-label="Notifications">
        🔔{unread > 0 && <span className="bell-dot">{unread}</span>}
      </button>
      {open && (
        <Modal
          title="Notifications"
          onClose={() => setOpen(false)}
          width={420}
          footer={
            <button className="btn btn--ghost btn--sm" onClick={markAll}>
              Mark all read
            </button>
          }
        >
          {items.length === 0 ? (
            <p className="muted">No notifications yet.</p>
          ) : (
            <div className="stack" style={{ gap: 8 }}>
              {items.map((n) => (
                <div key={n.id} className="listrow" style={{ background: n.is_read ? undefined : "var(--teal-50)" }}>
                  <div>
                    <div style={{ fontSize: 13.5 }}>{n.text}</div>
                    <div className="muted" style={{ fontSize: 11 }}>{timeAgo(n.created_at)}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Modal>
      )}
    </>
  );
}

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  if (!user) return null;
  const items = NAV[user.role] || [];

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">F</span>
          <span>FixFlow</span>
        </div>
        <span className="role-chip">{roleLabel(user.role)}</span>
        <div className="spacer" />
        <Bell />
        <div className="row" style={{ gap: 8 }}>
          <span className="muted" style={{ fontSize: 13 }}>{user.name}</span>
          <button
            className="btn btn--ghost btn--sm"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            Log out
          </button>
        </div>
      </header>
      <aside className="sidenav">
        {items.map((n) => (
          <NavLink key={n.to} to={n.to} end={n.end} className={({ isActive }) => `navlink ${isActive ? "active" : ""}`}>
            <span className="ic">{n.ic}</span>
            <span>{n.label}</span>
          </NavLink>
        ))}
        {user.role === "manager" && (
          <a className="navlink" href={`${API_BASE}/admin/`} target="_blank" rel="noopener">
            <span className="ic">⚙️</span>
            <span>Admin</span>
          </a>
        )}
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}

function roleLabel(role: Role): string {
  return { customer: "Customer", dispatcher: "Dispatcher", technician: "Technician", manager: "Manager", anonymous: "" }[role];
}
