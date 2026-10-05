"use client";

import { useRef, type ChangeEvent } from "react";

import { Icon } from "@/components/icon";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { acceptForField } from "@/lib/form-validation";
import { cn } from "@/lib/cn";
import { FILE_ACCEPT_LABEL, type FormField } from "@/types/forms";

type FormFieldInputProps = {
  field: FormField;
  value: string | number | string[] | File | null | undefined;
  error?: string;
  disabled?: boolean;
  onChange: (value: string | number | string[] | File | null) => void;
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FormFieldInput({ field, value, error, disabled, onChange }: FormFieldInputProps) {
  const helper = field.help_text ?? undefined;
  const label = field.label || "Untitled field";
  const required = Boolean(field.required && !disabled);

  if (field.type === "text" && field.multiline) {
    return (
      <Textarea
        cols={1}
        disabled={disabled}
        error={error}
        helper={helper}
        id={field.id}
        label={label}
        onChange={(event) => onChange(event.target.value)}
        required={required}
        rows={4}
        value={typeof value === "string" ? value : ""}
      />
    );
  }

  if (field.type === "text") {
    return (
      <Input
        disabled={disabled}
        error={error}
        helper={helper}
        id={field.id}
        label={label}
        maxLength={field.max_length}
        onChange={(event) => onChange(event.target.value)}
        required={required}
        type="text"
        value={typeof value === "string" ? value : ""}
      />
    );
  }

  if (field.type === "number") {
    return (
      <Input
        disabled={disabled}
        error={error}
        helper={helper}
        id={field.id}
        label={label}
        max={field.max ?? undefined}
        min={field.min ?? undefined}
        onChange={(event) => {
          const next = event.target.value;
          onChange(next === "" ? "" : Number(next));
        }}
        required={required}
        step={field.integer_only ? 1 : "any"}
        type="number"
        value={typeof value === "number" || typeof value === "string" ? value : ""}
      />
    );
  }

  if (field.type === "dropdown") {
    return (
      <div className="min-w-0 max-w-full">
        <label className="mb-1.5 block min-w-0 text-label-md font-medium break-words text-on-surface" htmlFor={field.id}>
          {label}
          {field.required ? (
            <span className="text-error" aria-hidden>
              {" "}
              *
            </span>
          ) : null}
        </label>
        <select
          className={cn(
            "box-border w-full min-w-0 max-w-full rounded-md border bg-surface-container-lowest px-3.5 py-2.5 text-body-md text-on-surface outline-none",
            error
              ? "border-error focus:border-error focus:ring-[3px] focus:ring-error/15"
              : "border-outline-variant focus:border-secondary focus:ring-[3px] focus:ring-secondary/15",
          )}
          disabled={disabled}
          id={field.id}
          onChange={(event) => onChange(event.target.value)}
          required={required}
          value={typeof value === "string" ? value : ""}
        >
          <option value="">Select…</option>
          {field.options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
        {error ? <p className="mt-1 text-body-sm text-error">{error}</p> : helper ? (
          <p className="mt-1 text-body-sm text-on-surface-variant">{helper}</p>
        ) : null}
      </div>
    );
  }

  if (field.type === "radio") {
    return (
      <fieldset className="min-w-0 max-w-full">
        <legend className="mb-1.5 min-w-0 text-label-md font-medium break-words text-on-surface">
          {label}
          {field.required ? (
            <span className="text-error" aria-hidden>
              {" "}
              *
            </span>
          ) : null}
        </legend>
        <div className="flex flex-col gap-2">
          {field.options.map((option) => (
            <label className="flex min-w-0 cursor-pointer items-center gap-space-sm" key={option}>
              <input
                checked={value === option}
                className="size-4 border-outline"
                disabled={disabled}
                name={field.id}
                onChange={() => onChange(option)}
                type="radio"
              />
              <span className="min-w-0 break-words text-body-md text-on-surface">{option}</span>
            </label>
          ))}
        </div>
        {error ? <p className="mt-1 text-body-sm text-error">{error}</p> : helper ? (
          <p className="mt-1 text-body-sm text-on-surface-variant">{helper}</p>
        ) : null}
      </fieldset>
    );
  }

  if (field.type === "checkboxes") {
    const selected = Array.isArray(value) ? value : [];
    return (
      <fieldset className="min-w-0 max-w-full">
        <legend className="mb-1.5 min-w-0 text-label-md font-medium break-words text-on-surface">
          {label}
          {field.required ? (
            <span className="text-error" aria-hidden>
              {" "}
              *
            </span>
          ) : null}
        </legend>
        <div className="flex flex-col gap-2">
          {field.options.map((option) => {
            const checked = selected.includes(option);
            return (
              <label className="flex min-w-0 cursor-pointer items-center gap-space-sm" key={option}>
                <input
                  checked={checked}
                  className="size-4 rounded border-outline"
                  disabled={disabled}
                  onChange={() => {
                    onChange(
                      checked ? selected.filter((item) => item !== option) : [...selected, option],
                    );
                  }}
                  type="checkbox"
                />
                <span className="min-w-0 break-words text-body-md text-on-surface">{option}</span>
              </label>
            );
          })}
        </div>
        {error ? <p className="mt-1 text-body-sm text-error">{error}</p> : helper ? (
          <p className="mt-1 text-body-sm text-on-surface-variant">{helper}</p>
        ) : null}
      </fieldset>
    );
  }

  if (field.type !== "file") {
    return null;
  }

  return (
    <FileFieldInput
      disabled={disabled}
      error={error}
      field={field}
      helper={helper}
      label={label}
      onChange={onChange}
      value={value instanceof File ? value : null}
    />
  );
}

function FileFieldInput({
  field,
  label,
  helper,
  error,
  disabled,
  value,
  onChange,
}: {
  field: Extract<FormField, { type: "file" }>;
  label: string;
  helper?: string;
  error?: string;
  disabled?: boolean;
  value: File | null;
  onChange: (value: File | null) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  function onFileInput(event: ChangeEvent<HTMLInputElement>) {
    onChange(event.target.files?.[0] ?? null);
    event.target.value = "";
  }

  return (
    <div className="min-w-0 max-w-full">
      <p className="mb-1.5 block min-w-0 text-label-md font-medium break-words text-on-surface">
        {label}
        {field.required ? (
          <span className="text-error" aria-hidden>
            {" "}
            *
          </span>
        ) : null}
      </p>
      <input
        accept={acceptForField(field)}
        className="sr-only"
        disabled={disabled}
        onChange={onFileInput}
        ref={inputRef}
        type="file"
      />
      <button
        className="w-full rounded-xl border-2 border-dashed border-outline-variant bg-surface-bright p-space-md text-center hover:border-secondary"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        type="button"
      >
        <Icon className="text-[24px] text-secondary" name="attach_file" />
        <p className="mt-1 text-label-md text-on-surface">Choose a file</p>
        <p className="mt-0.5 text-body-sm text-outline">
          {field.accept.map((item) => FILE_ACCEPT_LABEL[item]).join(", ")} • Max 5 MB
        </p>
      </button>
      {value ? (
        <div className="mt-space-sm flex items-center justify-between rounded-lg border border-outline-variant bg-surface-container-low p-space-sm">
          <div className="min-w-0">
            <p className="truncate text-label-md text-on-surface">{value.name}</p>
            <p className="text-body-sm text-on-surface-variant">{formatFileSize(value.size)}</p>
          </div>
          <button
            aria-label="Remove file"
            className="rounded p-1 text-outline hover:text-error"
            disabled={disabled}
            onClick={() => onChange(null)}
            type="button"
          >
            <Icon name="close" />
          </button>
        </div>
      ) : null}
      {error ? <p className="mt-1 text-body-sm text-error">{error}</p> : helper ? (
        <p className="mt-1 text-body-sm text-on-surface-variant">{helper}</p>
      ) : null}
    </div>
  );
}
