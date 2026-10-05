import Link from "next/link";
import type { ReactNode } from "react";

import { Brand } from "@/components/brand";
import { RequireGuest } from "@/components/require-guest";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <RequireGuest>
      <div className="flex min-h-screen flex-col items-center justify-center bg-surface px-margin-sm py-space-xl sm:px-margin">
        <header className="mb-space-lg flex w-full max-w-md flex-col items-center text-center">
          <Link href="/">
            <Brand size="auth" />
          </Link>
          <p className="mt-space-xs text-body-sm font-medium text-on-surface-variant">
            AI resume-screening middleware. Not an ATS.
          </p>
        </header>
        <div className="w-full max-w-md rounded-xl border border-outline-variant bg-surface-container-lowest p-6 shadow-sm sm:p-8">
          {children}
        </div>
      </div>
    </RequireGuest>
  );
}
