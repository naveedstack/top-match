import { useId, type InputHTMLAttributes, type ReactNode } from "react";

import { cn } from "@/lib/cn";

type InputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "className"> & {
  label: string;
  error?: string;
  helper?: string;
  trailing?: ReactNode;
  className?: string;
};

export function Input({
  id,
  label,
  error,
  helper,
  trailing,
  required,
  className,
  ...props
}: InputProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const describedBy = error ? `${inputId}-error` : helper ? `${inputId}-helper` : undefined;

  return (
    <div className="min-w-0 max-w-full">
      <label htmlFor={inputId} className="mb-1.5 block min-w-0 text-label-md font-medium break-words text-on-surface">
        {label}
        {required ? (
          <span className="text-error" aria-hidden>
            {" "}
            *
          </span>
        ) : null}
      </label>
      <div className="relative">
        <input
          id={inputId}
          required={required}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className={cn(
            "box-border w-full min-w-0 max-w-full rounded-md border bg-surface-container-lowest px-3.5 py-2.5 text-body-md text-on-surface outline-none transition duration-150",
            "placeholder:text-outline",
            error
              ? "border-error focus:border-error focus:ring-[3px] focus:ring-error/15"
              : "border-outline-variant focus:border-secondary focus:ring-[3px] focus:ring-secondary/15",
            trailing ? "pr-10" : null,
            className,
          )}
          {...props}
        />
        {trailing ? (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">{trailing}</div>
        ) : null}
      </div>
      {error ? (
        <p id={`${inputId}-error`} className="mt-1 text-body-sm text-error">
          {error}
        </p>
      ) : helper ? (
        <p id={`${inputId}-helper`} className="mt-1 text-body-sm text-on-surface-variant">
          {helper}
        </p>
      ) : null}
    </div>
  );
}
