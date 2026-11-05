import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../context/AuthContext.jsx";
import Alert from "./Alert.jsx";

function AppLayout() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [logoutError, setLogoutError] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);

  async function handleLogout() {
    setLogoutError("");
    setLoggingOut(true);
    try {
      await signOut();
      navigate("/login", { replace: true });
    } catch (error) {
      setLogoutError(error.message);
    } finally {
      setLoggingOut(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <Link className="brand" to="/" aria-label="SecureGate home">
          <span className="brand-mark" aria-hidden="true">S</span>
          <span>SecureGate</span>
        </Link>
        <nav className="site-nav" aria-label="Main navigation">
          {user ? (
            <>
              <NavLink to="/dashboard">Dashboard</NavLink>
              <NavLink to="/profile">Profile</NavLink>
              <button
                className="button button-quiet button-small"
                type="button"
                onClick={handleLogout}
                disabled={loggingOut}
              >
                {loggingOut ? "Signing out..." : "Log out"}
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login">Log in</NavLink>
              <Link className="button button-small" to="/register">
                Create account
              </Link>
            </>
          )}
        </nav>
      </header>
      <main className="main-content">
        <Alert>{logoutError}</Alert>
        <Outlet />
      </main>
      <footer className="site-footer">
        <span>SecureGate student portal</span>
        <span>Built with security in mind</span>
      </footer>
    </div>
  );
}

export default AppLayout;
