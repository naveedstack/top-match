"use client";

import { Icon } from "@/components/icon";
import { cn } from "@/lib/cn";
import { MAX_WEIGHT, type FormWarning, type GuardrailError } from "@/types/forms";

export const inputClass =
  "w-full min-w-0 max-w-full rounded-lg border border-outline-variant bg-surface-container-lowest px-3 py-1.5 text-body-md text-on-surface outline-none focus:border-secondary focus:ring-2 focus:ring-secondary/20 disabled:opacity-60";

export const smallInputClass =
  "w-16 rounded border border-outline-variant px-1.5 py-0.5 text-center font-mono text-xs disabled:opacity-60";

export function numberOrNull(raw: string): number | null {
  return raw === "" ? null : Number(raw);
}

export function ReasonInput({
  value,
  disabled,
  onChange,
}: {
  value: string;
  disabled: boolean;
  onChange: (reason: string) => void;
}) {
  return (
    <label className="block min-w-0">
      <span className="mb-1 block text-label-sm font-semibold text-on-surface">
        Reason shown to you when someone fails
      </span>
      <input
        className={inputClass}
        disabled={disabled}
        maxLength={300}
        onChange={(event) => onChange(event.target.value)}
        placeholder="e.g. Not authorized to work in Pakistan"
        type="text"
        value={value}
      />
    </label>
  );
}

export function WeightInput({
  weight,
  disabled,
  onChange,
}: {
  weight: number;
  disabled: boolean;
  onChange: (weight: number) => void;
}) {
  return (
    <label className="flex items-center gap-1.5 text-label-sm text-on-surface">
      Weight (0.5–{MAX_WEIGHT}):
      <input
        className={smallInputClass}
        disabled={disabled}
        max={MAX_WEIGHT}
        min={0.5}
        onChange={(event) => onChange(Number(event.target.value) || 1)}
        step={0.5}
        type="number"
        value={weight}
      />
    </label>
  );
}

export function Switch({
  checked,
  disabled,
  label,
  onChange,
}: {
  checked: boolean;
  disabled: boolean;
  label: string;
  onChange: (checked: boolean) => void;
}) {
  return (
    <button
      aria-checked={checked}
      className={cn(
        "flex min-w-0 items-center gap-2 text-left",
        disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer",
      )}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      role="switch"
      type="button"
    >
      <span
        className={cn(
          "relative inline-flex h-4 w-8 shrink-0 rounded-full transition-colors",
          checked ? "bg-secondary" : "bg-outline-variant",
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 size-3 rounded-full bg-surface-container-lowest shadow-sm transition-[left]",
            checked ? "left-4" : "left-0.5",
          )}
        />
      </span>
      <span className="text-label-sm font-medium text-on-surface">{label}</span>
    </button>
  );
}

/** Warnings never block saving; guardrail errors block it until the field changes. */
export function FieldNotices({
  warnings,
  blocked,
}: {
  warnings: FormWarning[];
  blocked: GuardrailError[];
}) {
  return (
    <>
      {blocked.map((item) => (
        <p
          className="mt-3 flex items-start gap-1.5 rounded-lg border border-error/30 bg-error-container/40 p-2.5 text-body-sm text-error"
          key={`${item.category}-${item.message}`}
          role="alert"
        >
          <Icon className="mt-0.5 shrink-0 text-[16px]" name="block" />
          <span>
            {item.message} <span className="font-semibold">{item.suggestion}</span>
          </span>
        </p>
      ))}
      {warnings.map((warning) => (
        <p
          className="mt-3 flex items-start gap-1.5 rounded-lg border border-status-knocked-out/30 bg-status-knocked-out-container p-2.5 text-body-sm text-status-knocked-out"
          key={warning.message}
          role="status"
        >
          <Icon className="mt-0.5 shrink-0 text-[16px]" name="warning" />
          {warning.message}
        </p>
      ))}
    </>
  );
}
