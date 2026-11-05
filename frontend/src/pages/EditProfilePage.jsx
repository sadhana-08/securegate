import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api.js";
import Alert from "../components/Alert.jsx";
import Loading from "../components/Loading.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { validateProfile } from "../validation.js";

function EditProfilePage() {
  const { setUser } = useAuth();
  const navigate = useNavigate();
  const [values, setValues] = useState({ full_name: "", email: "" });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let active = true;
    api.profile()
      .then((profile) => {
        if (active) {
          setValues({ full_name: profile.full_name, email: profile.email });
        }
      })
      .catch((requestError) => {
        if (active) {
          setError(requestError.message);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  function updateField(event) {
    setValues((current) => ({ ...current, [event.target.name]: event.target.value }));
    setErrors((current) => ({ ...current, [event.target.name]: "" }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    const validationErrors = validateProfile(values);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }
    setSubmitting(true);
    try {
      const updatedProfile = await api.updateProfile({
        full_name: values.full_name,
        email: values.email,
      });
      setUser({
        id: updatedProfile.id,
        username: updatedProfile.username,
        email: updatedProfile.email,
        full_name: updatedProfile.full_name,
      });
      navigate("/profile", { replace: true });
    } catch (requestError) {
      setError(requestError.message);
      if (requestError.details) {
        setErrors(requestError.details);
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return <Loading label="Loading profile editor..." />;
  }

  return (
    <section className="page-card narrow-card">
      <p className="eyebrow">Account settings</p>
      <h1>Edit profile</h1>
      <p className="muted">Update your name or email address.</p>
      <Alert>{error}</Alert>
      <form className="form-stack" onSubmit={handleSubmit} noValidate>
        <label className="field">
          <span>Full name</span>
          <input name="full_name" autoComplete="name" value={values.full_name} onChange={updateField} required />
          {errors.full_name && <small className="field-error">{errors.full_name}</small>}
        </label>
        <label className="field">
          <span>Email</span>
          <input name="email" type="email" autoComplete="email" value={values.email} onChange={updateField} required />
          {errors.email && <small className="field-error">{errors.email}</small>}
        </label>
        <div className="form-actions">
          <Link className="button button-secondary" to="/profile">Cancel</Link>
          <button className="button" type="submit" disabled={submitting}>
            {submitting ? "Saving..." : "Save changes"}
          </button>
        </div>
      </form>
    </section>
  );
}

export default EditProfilePage;
