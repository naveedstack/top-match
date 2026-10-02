"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { type ReactNode } from "react";

import { Brand } from "@/components/brand";
import { useAuth } from "@/context/auth-context";
import { cn } from "@/lib/cn";

export function RecruiterShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const jobsActive = pathname === "/jobs" || pathname.startsWith("/jobs/");

  async function onLogout() {
    await logout();
    router.replace("/login");
  }

  return (
    <div className="flex min-h-screen flex-col bg-surface text-on-surface">
      <header className="sticky top-0 z-30 flex h-14 w-full items-center justify-between border-b border-outline-variant bg-surface-container-lowest px-space-lg shadow-sm">
        <div className="flex items-center gap-space-md">
          <Brand size="nav" />
          {user?.company_name ? (
            <>
              <span className="text-outline-variant" aria-hidden>
                |
              </span>
              <span className="text-label-md font-semibold text-on-surface">{user.company_name}</span>
            </>
          ) : null}
        </div>
        <nav className="flex h-full items-center">
          <Link
            href="/jobs"
            className={cn(
              "flex h-full items-center px-space-sm",
              jobsActive
                ? "border-b-2 border-secondary text-headline-sm text-secondary"
                : "text-label-lg text-on-surface-variant hover:text-on-surface",
            )}
          >
            Jobs
          </Link>
        </nav>
        <button
          type="button"
          onClick={onLogout}
          className="text-label-md text-on-surface-variant transition-colors duration-150 hover:text-error"
        >
          Log out
        </button>
      </header>
      <main className="mx-auto flex w-full max-w-[1600px] flex-1 flex-col gap-space-lg px-space-lg py-space-lg">
        {children}
      </main>
    </div>
  );
}
