"use client";

import React, { createContext, useCallback, useContext, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { clearAuthTokenCookie } from "@/lib/auth";
import type { User } from "@/lib/types";

type AuthContextValue = {
  user: User | null;
  isLoading: boolean;
  logout: () => void;
  refetchMe: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const meQuery = useQuery({
    queryKey: ["auth", "me"],
    queryFn: () => apiFetch<User>("/auth/me"),
    retry: false
  });

  const logout = useCallback(() => {
    clearAuthTokenCookie();
    // Fast path: reload to force middleware redirect and clear cached state.
    window.location.href = "/login";
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: meQuery.data ?? null,
      isLoading: meQuery.isLoading,
      logout,
      refetchMe: () => void meQuery.refetch()
    }),
    [meQuery.data, meQuery.isLoading, logout, meQuery]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

