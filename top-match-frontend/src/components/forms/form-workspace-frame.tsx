import { type ReactNode } from "react";

import { cn } from "@/lib/cn";

export function FormWorkspaceFrame({
  subheader,
  builder,
  preview,
}: {
  subheader: ReactNode;
  builder: ReactNode;
  preview: ReactNode;
}) {
  return (
    <div className="flex h-full min-h-0 flex-1 flex-col overflow-hidden">
      <div className="shrink-0">{subheader}</div>
      <div
        className={cn(
          "grid min-h-0 flex-1 overflow-hidden",
          "grid-cols-1 grid-rows-2",
          "lg:grid-cols-[minmax(0,58%)_minmax(0,42%)] lg:grid-rows-1",
        )}
      >
        <div className="min-h-0 min-w-0 overflow-x-hidden overflow-y-auto overscroll-y-contain">{builder}</div>
        <div className="min-h-0 min-w-0 overflow-x-hidden overflow-y-auto overscroll-y-contain border-t border-outline-variant lg:border-t-0 lg:border-l">
          {preview}
        </div>
      </div>
    </div>
  );
}
