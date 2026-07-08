import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { homePathFor, useAuth } from "../auth";

const DEMO: [string, string][] = [
  ["Customer", "customer"],
  ["Dispatcher", "dispatcher"],
  ["Technician", "tech.ahmed"],
  ["Manager", "manager"],
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const user = await login(username, password);
      navigate(homePathFor(user.role));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-wrap">
      <div className="auth-card card">
        <div className="brand">
          <span className="brand-mark">F</span>
          <span>FixFlow</span>
        </div>
        <h2 style={{ textAlign: "center", margin: "8px 0 2px" }}>Sign in</h2>
        <p className="muted" style={{ textAlign: "center", fontSize: 13, marginTop: 0, marginBottom: 18 }}>
          Welcome back.
        </p>
        {error && <div className="form-error" style={{ marginBottom: 12 }}>{error}</div>}
        <form onSubmit={submit}>
          <div className="field">
            <label>Username</label>
            <input className="input" value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
          </div>
          <div className="field">
            <label>Password</label>
            <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <button className="btn btn--block" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
        </form>
        <p className="muted" style={{ textAlign: "center", fontSize: 13, marginTop: 14 }}>
          New customer?{" "}
          <Link to="/register" style={{ color: "var(--teal)", fontWeight: 600 }}>Create an account</Link>
        </p>
        <div className="demo-creds" style={{ marginTop: 16 }}>
          <b>Explore the demo</b> — one click fills a seeded login (password <span className="mono">demo12345</span>):
          <div className="cred-btns">
            {DEMO.map(([label, uname]) => (
              <button
                key={uname}
                type="button"
                className="chip"
                onClick={() => {
                  setUsername(uname);
                  setPassword("demo12345");
                }}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
