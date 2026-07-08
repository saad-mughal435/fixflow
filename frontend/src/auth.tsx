import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";

import { api, tokens } from "./api";
import type { User } from "./types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<User>;
  register: (payload: Record<string, unknown>) => Promise<User>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>(null as unknown as AuthContextValue);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      if (tokens.access) {
        try {
          setUser(await api.me());
        } catch {
          tokens.clear();
        }
      }
      setLoading(false);
    })();
  }, []);

  const login = async (username: string, password: string) => {
    const u = await api.login(username, password);
    setUser(u);
    return u;
  };
  const register = async (payload: Record<string, unknown>) => {
    const u = await api.register(payload);
    setUser(u);
    return u;
  };
  const logout = () => {
    tokens.clear();
    setUser(null);
  };
  const refreshUser = async () => {
    try {
      setUser(await api.me());
    } catch {
      /* ignore */
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

export function homePathFor(role: string): string {
  switch (role) {
    case "manager":
      return "/manage";
    case "dispatcher":
      return "/dispatch";
    case "technician":
      return "/jobs";
    default:
      return "/app";
  }
}
