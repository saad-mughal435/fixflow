import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../api";
import type { Category, Department, Property, RequestDetail } from "../../types";
import { Modal, useToast } from "../../ui";

const PRIORITIES: [string, string][] = [
  ["p1_emergency", "Emergency"],
  ["p2_urgent", "Urgent"],
  ["p3_routine", "Routine"],
  ["p4_low", "Low"],
];

export default function NewRequest() {
  const navigate = useNavigate();
  const toast = useToast();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [properties, setProperties] = useState<Property[]>([]);
  const [form, setForm] = useState({
    department: "", category: "", location: "", title: "", description: "", priority: "p3_routine",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [showProp, setShowProp] = useState(false);

  useEffect(() => {
    api.get<Department[]>("/api/departments/").then(setDepartments).catch(() => {});
    api.get<Property[]>("/api/properties/").then(setProperties).catch(() => {});
  }, []);

  useEffect(() => {
    if (!form.department) {
      setCategories([]);
      return;
    }
    api
      .get<Category[]>(`/api/categories/?department=${form.department}`)
      .then(setCategories)
      .catch(() => {});
    setForm((f) => ({ ...f, category: "" }));
  }, [form.department]);

  const set = (k: keyof typeof form, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.department || !form.title) {
      setError("Pick a department and describe the issue.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const payload = {
        department: Number(form.department),
        category: form.category ? Number(form.category) : null,
        location: form.location ? Number(form.location) : null,
        title: form.title,
        description: form.description,
        priority: form.priority,
      };
      const created = await api.post<RequestDetail>("/api/requests/", payload);
      toast(`Request ${created.reference} submitted`);
      navigate(`/requests/${created.reference}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit the request");
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <div className="page-head">
        <div>
          <h1>New request</h1>
          <div className="sub">Tell us what needs fixing — we’ll route it to the right team.</div>
        </div>
      </div>

      <div className="card" style={{ maxWidth: 640 }}>
        {error && <div className="form-error" style={{ marginBottom: 14 }}>{error}</div>}
        <form onSubmit={submit}>
          <div className="field">
            <label>Department</label>
            <select className="select" value={form.department} onChange={(e) => set("department", e.target.value)}>
              <option value="">Select a department…</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Type of work</label>
            <select
              className="select"
              value={form.category}
              onChange={(e) => set("category", e.target.value)}
              disabled={!form.department}
            >
              <option value="">{form.department ? "Select a category…" : "Pick a department first"}</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Property</label>
            <div className="row">
              <select className="select" value={form.location} onChange={(e) => set("location", e.target.value)}>
                <option value="">Select a property…</option>
                {properties.map((p) => (
                  <option key={p.id} value={p.id}>{p.label} — {p.community || p.city}</option>
                ))}
              </select>
              <button type="button" className="btn btn--ghost btn--sm" onClick={() => setShowProp(true)}>+ Add</button>
            </div>
          </div>

          <div className="field">
            <label>What needs fixing?</label>
            <input className="input" value={form.title} onChange={(e) => set("title", e.target.value)} placeholder="e.g. AC not cooling in the bedroom" />
          </div>

          <div className="field">
            <label>Details</label>
            <textarea className="textarea" value={form.description} onChange={(e) => set("description", e.target.value)} placeholder="Describe the issue and a convenient time for access…" />
          </div>

          <div className="field">
            <label>Priority</label>
            <div className="chips">
              {PRIORITIES.map(([v, label]) => (
                <button key={v} type="button" className={`chip ${form.priority === v ? "active" : ""}`} onClick={() => set("priority", v)}>
                  {label}
                </button>
              ))}
            </div>
          </div>

          <button className="btn" disabled={busy}>{busy ? "Submitting…" : "Submit request"}</button>
        </form>
      </div>

      {showProp && (
        <AddPropertyModal
          onClose={() => setShowProp(false)}
          onCreated={(p) => {
            setProperties((xs) => [...xs, p]);
            set("location", String(p.id));
            setShowProp(false);
            toast("Property added");
          }}
        />
      )}
    </>
  );
}

function AddPropertyModal({ onClose, onCreated }: { onClose: () => void; onCreated: (p: Property) => void }) {
  const [form, setForm] = useState({ label: "", property_type: "apartment", address_line: "", community: "", unit_number: "" });
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof form, v: string) => setForm((f) => ({ ...f, [k]: v }));
  const save = async () => {
    setBusy(true);
    try {
      const p = await api.post<Property>("/api/properties/", { ...form, city: "Dubai", emirate: "Dubai" });
      onCreated(p);
    } finally {
      setBusy(false);
    }
  };
  return (
    <Modal
      title="Add a property"
      onClose={onClose}
      footer={
        <>
          <button className="btn btn--ghost" onClick={onClose}>Cancel</button>
          <button className="btn" onClick={save} disabled={busy || !form.label || !form.address_line}>Save</button>
        </>
      }
    >
      <div className="field">
        <label>Label</label>
        <input className="input" value={form.label} onChange={(e) => set("label", e.target.value)} placeholder="Marina apartment" />
      </div>
      <div className="field">
        <label>Type</label>
        <select className="select" value={form.property_type} onChange={(e) => set("property_type", e.target.value)}>
          <option value="apartment">Apartment</option>
          <option value="villa">Villa</option>
          <option value="townhouse">Townhouse</option>
          <option value="office">Office</option>
          <option value="retail">Retail</option>
          <option value="other">Other</option>
        </select>
      </div>
      <div className="field">
        <label>Address</label>
        <input className="input" value={form.address_line} onChange={(e) => set("address_line", e.target.value)} placeholder="Building, street" />
      </div>
      <div className="field-row">
        <div className="field">
          <label>Community</label>
          <input className="input" value={form.community} onChange={(e) => set("community", e.target.value)} placeholder="Dubai Marina" />
        </div>
        <div className="field">
          <label>Unit no.</label>
          <input className="input" value={form.unit_number} onChange={(e) => set("unit_number", e.target.value)} />
        </div>
      </div>
    </Modal>
  );
}
