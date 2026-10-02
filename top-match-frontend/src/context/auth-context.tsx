"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useContext, useEffect, useMemo, useSyncExternalStore } from "react";

import {
  getMe,
  login as loginRequest,
  logout as logoutRequest,
  register as registerRequest,
  toRecruiter,
} from "@/api/auth";
import { subscribeSession } from "@/lib/auth-session";
import { queryKeys } from "@/lib/query-keys";
import { clearTokens, getRefreshToken, hasStoredSession, setTokens } from "@/lib/token-storage";
import type { LoginRequest, Recruiter, RegisterRequest } from "@/types/auth";

type AuthContextValue = {
  user: Recruiter | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (body: LoginRequest) => Promise<void>;
  register: (body: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
};

function getServerSession(): boolean {
  return false;
}

function subscribeHydration() {
  return () => {};
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const hydrated = useSyncExternalStore(subscribeHydration, () => true, getServerSession);
  const hasSession = useSyncExternalStore(subscribeSession, hasStoredSession, getServerSession);

  useEffect(() => {
    return subscribeSession(() => {
      if (!hasStoredSession()) {
        queryClient.clear();
      }
    });
  }, [queryClient]);

  const meQuery = useQuery({
    queryKey: queryKeys.auth.me,
    queryFn: getMe,
    enabled: hasSession,
    retry: false,
  });

  const value = useMemo<AuthContextValue>(() => {
    const user = meQuery.data ?? null;

    return {
      user,
      isAuthenticated: user !== null,
      isLoading: !hydrated || (hasSession && meQuery.isPending),
      login: async (body) => {
        const auth = await loginRequest(body);
        queryClient.setQueryData(queryKeys.auth.me, toRecruiter(auth));
        setTokens(auth);
      },
      register: async (body) => {
        const auth = await registerRequest(body);
        queryClient.setQueryData(queryKeys.auth.me, toRecruiter(auth));
        setTokens(auth);
      },
      logout: async () => {
        const refreshToken = getRefreshToken();
        try {
          if (refreshToken) {
            await logoutRequest(refreshToken);
          }
        } finally {
          clearTokens();
        }
      },
    };
  }, [hasSession, hydrated, meQuery.data, meQuery.isPending, queryClient]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (value === null) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return value;
}
