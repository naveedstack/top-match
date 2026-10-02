import type { ReactNode } from "react";

import { Brand } from "@/components/brand";
import { Icon } from "@/components/icon";

export default function ApplyLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-surface px-space-md py-space-xl">
      <div className="mx-auto flex w-full max-w-2xl flex-col gap-space-lg">
        <header className="flex items-center justify-between py-space-xs">
          <Brand />
          <div className="flex items-center gap-space-xs text-label-md text-on-surface-variant">
            <Icon className="text-[15px] text-secondary" name="lock" />
            <span>Secure Application Portal</span>
          </div>
        </header>
        {children}
      </div>
    </div>
  );
}
