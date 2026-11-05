import React from "react";
import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import Alert from "../components/Alert.jsx";
import Loading from "../components/Loading.jsx";
import { api } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";
import { validateRegistration } from "../validation.js";

const initialValues = {
  username: "",
  email: "",
  full_name: "",
  password: "",
};

function RegisterPage() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (loading) {
    return <Loading label="Checking your session..." />;
  }
  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  function updateField(event) {
    setValues((current) => ({ ...current, [event.target.name]: event.target.value }));
    setErrors((current) => ({ ...current, [event.target.name]: "" }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    const validationErrors = validateRegistration(values);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setSubmitting(true);
    try {
      const result = await api.register(values);
      navigate("/login", { replace: true, state: { notice: result.message } });
    } catch (requestError) {
      setError(requestError.message);
      if (requestError.details) {
        setErrors(requestError.details);
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="page-card auth-card">
      <p className="eyebrow">Get started</p>
      <h1>Create your account</h1>
      <p className="muted">A few details are all you need to get started.</p>
      <Alert>{error}</Alert>
      <form className="form-stack" onSubmit={handleSubmit} noValidate>
        <label className="field">
          <span>Full name</span>
          <input name="full_name" autoComplete="name" value={values.full_name} onChange={updateField} required />
          {errors.full_name && <small className="field-error">{errors.full_name}</small>}
        </label>
        <label className="field">
          <span>Username</span>
          <input name="username" autoComplete="username" value={values.username} onChange={updateField} required />
          {errors.username && <small className="field-error">{errors.username}</small>}
        </label>
        <label className="field">
          <span>Email</span>
          <input name="email" type="email" autoComplete="email" value={values.email} onChange={updateField} required />
          {errors.email && <small className="field-error">{errors.email}</small>}
        </label>
        <label className="field">
          <span>Password</span>
          <input name="password" type="password" autoComplete="new-password" value={values.password} onChange={updateField} required />
          <small className="field-hint">12-128 characters. The server will check password strength when you submit.</small>
          {errors.password && <small className="field-error">{errors.password}</small>}
        </label>
        <button className="button button-wide" type="submit" disabled={submitting}>
          {submitting ? "Creating account..." : "Create account"}
        </button>
      </form>
      <p className="form-footnote">
        Already registered? <Link to="/login">Log in</Link>
      </p>
    </section>
  );
}

export default RegisterPage;
