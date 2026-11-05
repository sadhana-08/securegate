import { Link } from "react-router-dom";

function NotFoundPage() {
  return (
    <section className="page-card narrow-card centered-card">
      <p className="eyebrow">404 · Page not found</p>
      <h1>This page isn’t here</h1>
      <p className="muted">The address may be incorrect, or the page may have moved.</p>
      <Link className="button" to="/dashboard">Return to dashboard</Link>
    </section>
  );
}

export default NotFoundPage;
