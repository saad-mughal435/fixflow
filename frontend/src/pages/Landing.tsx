import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div className="landing">
      <nav className="landing-nav">
        <div className="brand">
          <span className="brand-mark">F</span>
          <span>FixFlow</span>
        </div>
        <div className="spacer" />
        <Link className="btn btn--ghost btn--sm" to="/login">Staff sign in</Link>
      </nav>

      <div className="hero">
        <h1>Property maintenance, handled.</h1>
        <p>
          Raise a maintenance request in seconds. FixFlow routes it to the right team, assigns a
          skilled technician, and keeps you posted until the job is done.
        </p>
        <div className="hero-cta">
          <Link className="btn" to="/register">Raise a request</Link>
          <Link className="btn btn--ghost" to="/login">Sign in</Link>
        </div>
      </div>

      <div className="steps">
        <div className="step">
          <div className="n">1</div>
          <h4>You raise it</h4>
          <p>Pick the department — plumbing, electrical, AC, and more — describe the issue, and choose your property.</p>
        </div>
        <div className="step">
          <div className="n">2</div>
          <h4>The team receives it</h4>
          <p>Your request lands in the right department's inbox with an SLA clock running.</p>
        </div>
        <div className="step">
          <div className="n">3</div>
          <h4>A technician is assigned</h4>
          <p>A dispatcher assigns a technician who actually holds that skill — one person, many skills.</p>
        </div>
        <div className="step">
          <div className="n">4</div>
          <h4>You track it live</h4>
          <p>Watch the status move from received to in-progress to completed, with updates along the way.</p>
        </div>
      </div>

      <p className="muted" style={{ textAlign: "center", padding: "16px 0 44px", fontSize: 13 }}>
        Working prototype · Django + DRF API · React SPA · PostgreSQL · JWT auth
      </p>
    </div>
  );
}
