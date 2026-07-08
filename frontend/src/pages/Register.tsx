import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../auth";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    first_name: "", last_name: "", username: "", email: "", phone: "", password: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (k: keyof typeof form) => (e: { target: { value: string } }) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await register(form);
      navigate("/app");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
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
        <h2 style={{ textAlign: "center", margin: "8px 0 2px" }}>Create your account</h2>
        <p className="muted" style={{ textAlign: "center", fontSize: 13, marginTop: 0, marginBottom: 18 }}>
          Raise and track maintenance requests for your properties.
        </p>
        {error && <div className="form-error" style={{ marginBottom: 12 }}>{error}</div>}
        <form onSubmit={submit}>
          <div className="field-row">
            <div className="field">
              <label>First name</label>
              <input className="input" value={form.first_name} onChange={set("first_name")} autoFocus />
            </div>
            <div className="field">
              <label>Last name</label>
              <input className="input" value={form.last_name} onChange={set("last_name")} />
            </div>
          </div>
          <div className="field">
            <label>Username</label>
            <input className="input" value={form.username} onChange={set("username")} required />
          </div>
          <div className="field">
            <label>Email</label>
            <input className="input" type="email" value={form.email} onChange={set("email")} required />
          </div>
          <div className="field">
            <label>Phone (optional)</label>
            <input className="input" value={form.phone} onChange={set("phone")} placeholder="+9715…" />
          </div>
          <div className="field">
            <label>Password</label>
            <input className="input" type="password" value={form.password} onChange={set("password")} required />
          </div>
          <button className="btn btn--block" disabled={busy}>{busy ? "Creating…" : "Create account"}</button>
        </form>
        <p className="muted" style={{ textAlign: "center", fontSize: 13, marginTop: 14 }}>
          Already have an account?{" "}
          <Link to="/login" style={{ color: "var(--teal)", fontWeight: 600 }}>Sign in</Link>
        </p>
      </div>
    </div>
  );
}
