import { cn } from "@/lib/cn";

type IconProps = {
  name: string;
  className?: string;
};

export function Icon({ name, className }: IconProps) {
  return (
    <span className={cn("material-symbols-outlined", className)} aria-hidden>
      {name}
    </span>
  );
}
