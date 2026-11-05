import React from "react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import Alert from "../components/Alert.jsx";
import Loading from "../components/Loading.jsx";

function ProfilePage() {
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadProfile() {
    setLoading(true);
    setError("");
    try {
      setProfile(await api.profile());
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProfile();
  }, []);

  if (loading) {
    return <Loading label="Loading your profile..." />;
  }

  return (
    <section className="page-card narrow-card">
      <div className="page-heading-row">
        <div>
          <p className="eyebrow">Your account</p>
          <h1>Profile</h1>
        </div>
        {profile && <Link className="button button-secondary" to="/profile/edit">Edit profile</Link>}
      </div>
      <Alert>{error}</Alert>
      {error && <button className="button button-secondary" type="button" onClick={loadProfile}>Try again</button>}
      {profile && (
        <dl className="profile-list">
          <div><dt>Full name</dt><dd>{profile.full_name}</dd></div>
          <div><dt>Username</dt><dd>{profile.username}</dd></div>
          <div><dt>Email</dt><dd>{profile.email}</dd></div>
          <div><dt>Member since</dt><dd>{profile.created_at}</dd></div>
        </dl>
      )}
    </section>
  );
}

export default ProfilePage;
