import type { ReactNode } from "react";

import { Icon } from "@/components/icon";

type BannerProps = {
  children: ReactNode;
};

export function Banner({ children }: BannerProps) {
  return (
    <div className="flex items-start gap-space-sm rounded-lg border border-outline-variant bg-surface-container-lowest p-space-sm shadow-sm md:items-center md:px-space-md">
      <Icon name="info" className="shrink-0 text-secondary" />
      <div className="text-label-md text-on-surface-variant">{children}</div>
    </div>
  );
}
