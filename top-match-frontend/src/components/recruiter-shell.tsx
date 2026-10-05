"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useLayoutEffect, type ReactNode } from "react";

import { Brand } from "@/components/brand";
import { useAuth } from "@/context/auth-context";
import { cn } from "@/lib/cn";

export function RecruiterShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const jobsActive = pathname === "/jobs" || pathname.startsWith("/jobs/");
  const formWorkspace = pathname === "/jobs/new" || /^\/jobs\/[^/]+\/form$/.test(pathname);

  useLayoutEffect(() => {
    if (!formWorkspace) {
      return;
    }
    const html = document.documentElement;
    html.classList.add("overflow-hidden");
    document.body.classList.add("h-dvh", "overflow-hidden");
    return () => {
      html.classList.remove("overflow-hidden");
      document.body.classList.remove("h-dvh", "overflow-hidden");
    };
  }, [formWorkspace]);

  async function onLogout() {
    await logout();
    router.replace("/login");
  }

  return (
    <div
      className={cn(
        "flex flex-col bg-surface text-on-surface",
        formWorkspace ? "h-dvh max-h-dvh min-h-0 flex-1 overflow-hidden" : "min-h-screen",
      )}
    >
      <header className="sticky top-0 z-30 flex h-14 w-full shrink-0 items-center justify-between border-b border-outline-variant bg-surface-container-lowest px-space-lg shadow-sm">
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
      <main
        className={cn(
          "flex w-full flex-1 flex-col",
          formWorkspace
            ? "h-[calc(100dvh-3.5rem)] min-h-0 overflow-hidden p-0"
            : "mx-auto max-w-[1600px] gap-space-lg px-space-lg py-space-lg",
        )}
      >
        {children}
      </main>
    </div>
  );
}
