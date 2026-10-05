import { useId, type ReactNode, type TextareaHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

type TextareaProps = Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "className"> & {
  label: string;
  error?: string;
  helper?: string;
  className?: string;
  extra?: ReactNode;
};

export function Textarea({
  id,
  label,
  error,
  helper,
  required,
  className,
  extra,
  disabled,
  ...props
}: TextareaProps) {
  const generatedId = useId();
  const textareaId = id ?? generatedId;
  const describedBy = error ? `${textareaId}-error` : helper ? `${textareaId}-helper` : undefined;

  return (
    <div className="min-w-0 max-w-full">
      <div className="mb-1.5 flex items-center justify-between gap-space-sm">
        <label htmlFor={textareaId} className="block min-w-0 text-label-md font-medium break-words text-on-surface">
          {label}
          {required ? (
            <span className="text-error" aria-hidden>
              {" "}
              *
            </span>
          ) : null}
        </label>
        {extra}
      </div>
      <textarea
        id={textareaId}
        required={required}
        disabled={disabled}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={cn(
          "box-border block w-full min-w-0 max-w-full overflow-x-hidden break-words rounded-md border bg-surface-container-lowest px-3.5 py-2.5 text-body-md text-on-surface outline-none transition duration-150",
          "[field-sizing:fixed]",
          "placeholder:text-outline",
          disabled ? "resize-none" : "resize-y",
          error
            ? "border-error focus:border-error focus:ring-[3px] focus:ring-error/15"
            : "border-outline-variant focus:border-secondary focus:ring-[3px] focus:ring-secondary/15",
          className,
        )}
        {...props}
        cols={1}
      />
      {error ? (
        <p id={`${textareaId}-error`} className="mt-1 text-body-sm text-error">
          {error}
        </p>
      ) : helper ? (
        <p id={`${textareaId}-helper`} className="mt-1 text-body-sm text-on-surface-variant">
          {helper}
        </p>
      ) : null}
    </div>
  );
}
