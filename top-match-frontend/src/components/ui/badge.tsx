import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export type BadgeVariant =
  | "open"
  | "closed"
  | "received"
  | "processing"
  | "scored"
  | "refused"
  | "failed";

type BadgeProps = {
  variant: BadgeVariant;
  children?: ReactNode;
};

const variantClass: Record<BadgeVariant, { wrap: string; dot: string }> = {
  open: {
    wrap: "bg-status-scored-container text-status-scored",
    dot: "bg-status-scored",
  },
  closed: {
    wrap: "bg-status-refused-container text-status-refused",
    dot: "bg-status-refused",
  },
  received: {
    wrap: "bg-status-received-container text-status-received",
    dot: "bg-status-received",
  },
  processing: {
    wrap: "bg-status-processing-container text-status-processing",
    dot: "bg-status-processing",
  },
  scored: {
    wrap: "bg-status-scored-container text-status-scored",
    dot: "bg-status-scored",
  },
  refused: {
    wrap: "bg-status-refused-container text-status-refused",
    dot: "bg-status-refused",
  },
  failed: {
    wrap: "bg-status-failed-container text-status-failed",
    dot: "bg-status-failed",
  },
};

const defaultLabel: Record<BadgeVariant, string> = {
  open: "Open",
  closed: "Closed",
  received: "Received",
  processing: "Processing",
  scored: "Scored",
  refused: "Refused",
  failed: "Failed",
};

export function Badge({ variant, children }: BadgeProps) {
  const styles = variantClass[variant];

  return (
    <span
      className={cn(
        "inline-flex h-[22px] items-center gap-1.5 rounded px-2 text-label-sm",
        styles.wrap,
      )}
    >
      <span className={cn("size-1.5 rounded-full", styles.dot)} />
      {children ?? defaultLabel[variant]}
    </span>
  );
}
