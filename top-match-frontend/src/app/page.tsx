"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { LoadingScreen } from "@/components/loading-screen";
import { LandingPage } from "@/components/marketing/landing-page";
import { useAuth } from "@/context/auth-context";

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading || !isAuthenticated) {
      return;
    }
    router.replace("/jobs");
  }, [isAuthenticated, isLoading, router]);

  if (isLoading || isAuthenticated) {
    return <LoadingScreen />;
  }

  return <LandingPage />;
}
