import React from "react";

function Alert({ children, variant = "error" }) {
  if (!children) {
    return null;
  }
  return (
    <div className={`alert alert-${variant}`} role="alert">
      {children}
    </div>
  );
}

export default Alert;
