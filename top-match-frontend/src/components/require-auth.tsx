"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { LoadingScreen } from "@/components/loading-screen";
import { useAuth } from "@/context/auth-context";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading || !isAuthenticated) {
    return <LoadingScreen />;
  }

  return children;
}
