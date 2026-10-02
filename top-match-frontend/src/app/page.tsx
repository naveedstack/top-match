"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { LoadingScreen } from "@/components/loading-screen";
import { useAuth } from "@/context/auth-context";

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) {
      return;
    }
    router.replace(isAuthenticated ? "/jobs" : "/login");
  }, [isAuthenticated, isLoading, router]);

  return <LoadingScreen />;
}
