import { cn } from "@/lib/cn";

type IconProps = {
  name: string;
  className?: string;
};

export function Icon({ name, className }: IconProps) {
  return (
    <span
      aria-hidden
      className={cn("material-symbols-outlined leading-none", className)}
    >
      {name}
    </span>
  );
}
