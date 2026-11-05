import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

function DashboardPage() {
  const { user } = useAuth();

  return (
    <section className="page-card">
      <p className="eyebrow">Student portal</p>
      <h1>Welcome, {user.full_name}</h1>
      <p className="muted">
        You are signed in as <strong>{user.username}</strong>. Your SecureGate
        dashboard is ready.
      </p>
      <div className="dashboard-grid">
        <article className="info-card">
          <span className="info-icon" aria-hidden="true">01</span>
          <h2>Your profile</h2>
          <p>Review the contact details associated with your account.</p>
          <Link className="text-link" to="/profile">View profile</Link>
        </article>
        <article className="info-card">
          <span className="info-icon" aria-hidden="true">02</span>
          <h2>Account security</h2>
          <p>Your account uses secure sessions and protected profile access.</p>
          <span className="security-label">Session protected</span>
        </article>
      </div>
    </section>
  );
}

export default DashboardPage;
