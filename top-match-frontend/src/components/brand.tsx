import { Icon } from "@/components/icon";
import { cn } from "@/lib/cn";

type BrandProps = {
  size?: "auth" | "nav";
};

export function Brand({ size = "nav" }: BrandProps) {
  const auth = size === "auth";

  return (
    <div className="inline-flex items-center gap-space-xs">
      <div
        className={cn(
          "flex size-7 items-center justify-center text-on-primary",
          auth ? "rounded-lg bg-primary-container" : "rounded-lg bg-primary",
        )}
      >
        <Icon name="fact_check" className="text-[18px]" />
      </div>
      <span
        className={cn(
          "tracking-tight text-on-surface",
          auth ? "text-headline-lg font-bold" : "text-headline-md font-semibold",
        )}
      >
        Top Match
      </span>
    </div>
  );
}
