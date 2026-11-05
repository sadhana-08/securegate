import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "../api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const refreshUser = useCallback(async () => {
    setLoading(true);
    setLoadError("");
    try {
      const currentUser = await api.me();
      setUser(currentUser);
      return currentUser;
    } catch (error) {
      if (error.status === 401) {
        setUser(null);
      } else {
        setLoadError(error.message);
      }
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser().catch(() => {});
  }, [refreshUser]);

  const signIn = useCallback(async (identifier, password) => {
    await api.login(identifier, password);
    return refreshUser();
  }, [refreshUser]);

  const signOut = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      setUser(null);
    }
  }, []);

  const value = {
    user,
    setUser,
    loading,
    loadError,
    refreshUser,
    signIn,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }
  return context;
}
