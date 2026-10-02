import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

type ButtonVariant = "primary" | "secondary" | "outline" | "destructive";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  pending?: boolean;
};

const variantClass: Record<ButtonVariant, string> = {
  primary: "border-transparent bg-primary text-on-primary hover:bg-inverse-surface",
  secondary: "border-transparent bg-secondary text-on-secondary hover:bg-on-secondary-fixed-variant",
  outline:
    "border-outline-variant bg-surface-container-lowest text-on-surface-variant hover:border-outline hover:bg-surface",
  destructive:
    "border-status-failed-border bg-surface-container-lowest text-status-failed hover:bg-status-failed-container",
};

export function Button({
  variant = "primary",
  pending = false,
  disabled,
  className,
  children,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || pending}
      aria-busy={pending || undefined}
      className={cn(
        "inline-flex items-center justify-center gap-space-xs rounded-lg border px-space-md py-2.5 text-label-lg transition-colors duration-150",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary focus-visible:ring-offset-2",
        "disabled:pointer-events-none disabled:opacity-50",
        variantClass[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
