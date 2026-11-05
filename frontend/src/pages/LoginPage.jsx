import React from "react";
import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import Alert from "../components/Alert.jsx";
import Loading from "../components/Loading.jsx";
import { useAuth } from "../context/AuthContext.jsx";

function LoginPage() {
  const { user, loading, signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const notice = location.state?.notice || "";
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (loading) {
    return <Loading label="Checking your session..." />;
  }
  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    if (!identifier.trim() || !password) {
      setError("Enter your username or email and password.");
      return;
    }
    setSubmitting(true);
    try {
      await signIn(identifier.trim(), password);
      navigate(location.state?.from?.pathname || "/dashboard", { replace: true });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="page-card auth-card">
      <p className="eyebrow">Welcome back</p>
      <h1>Log in to SecureGate</h1>
      <p className="muted">Use your student account to continue.</p>
      {notice && <Alert variant="success">{notice}</Alert>}
      <Alert>{error}</Alert>
      <form className="form-stack" onSubmit={handleSubmit} noValidate>
        <label className="field">
          <span>Username or email</span>
          <input
            autoComplete="username"
            value={identifier}
            onChange={(event) => setIdentifier(event.target.value)}
            required
          />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        <button className="button button-wide" type="submit" disabled={submitting}>
          {submitting ? "Logging in..." : "Log in"}
        </button>
      </form>
      <p className="form-footnote">
        New to SecureGate? <Link to="/register">Create an account</Link>
      </p>
    </section>
  );
}

export default LoginPage;
