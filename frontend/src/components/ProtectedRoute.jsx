import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import Alert from "./Alert.jsx";
import Loading from "./Loading.jsx";

function ProtectedRoute() {
  const { user, loading, loadError, refreshUser } = useAuth();
  const location = useLocation();

  if (loading) {
    return <Loading label="Checking your session..." />;
  }
  if (loadError) {
    return (
      <section className="page-card narrow-card">
        <Alert>{loadError}</Alert>
        <button className="button" type="button" onClick={() => refreshUser().catch(() => {})}>
          Try again
        </button>
      </section>
    );
  }
  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return <Outlet />;
}

export default ProtectedRoute;
