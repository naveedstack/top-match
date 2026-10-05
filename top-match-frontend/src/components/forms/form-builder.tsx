"use client";

import { useState } from "react";

import { FormFieldInput } from "@/components/forms/form-field-input";
import { Icon } from "@/components/icon";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/cn";
import {
  FILE_ACCEPT_LABEL,
  FORM_FIELD_TYPES,
  MAX_FILE_FIELDS,
  MAX_FORM_FIELDS,
  newFormField,
  type FileAccept,
  type FormField,
  type FormFieldType,
} from "@/types/forms";

const FILE_ACCEPTS: FileAccept[] = ["pdf", "docx", "png", "jpeg"];

const LOCKED_ROWS = [
  { icon: "mail", title: "Email address", detail: "Always required. Identifies the application." },
  { icon: "picture_as_pdf", title: "Resume PDF", detail: "Always required. Used for AI scoring." },
  { icon: "verified_user", title: "Consent", detail: "Always required. Privacy and AI-screening notice." },
];

type FormBuilderProps = {
  fields: FormField[];
  onChange: (fields: FormField[]) => void;
  disabled?: boolean;
  error?: string;
};

export function FormBuilder({ fields, onChange, disabled = false, error }: FormBuilderProps) {
  const [tab, setTab] = useState<"build" | "preview">("build");
  const [previewValues, setPreviewValues] = useState<
    Record<string, string | number | string[] | File | null>
  >({});
  const fileCount = fields.filter((field) => field.type === "file").length;
  const atFieldCap = fields.length >= MAX_FORM_FIELDS;

  function updateField(id: string, next: FormField) {
    onChange(fields.map((field) => (field.id === id ? next : field)));
  }

  function addField(type: FormFieldType) {
    if (disabled || atFieldCap) {
      return;
    }
    if (type === "file" && fileCount >= MAX_FILE_FIELDS) {
      return;
    }
    onChange([...fields, newFormField(type)]);
  }

  function moveField(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= fields.length) {
      return;
    }
    const next = [...fields];
    const [item] = next.splice(index, 1);
    next.splice(target, 0, item);
    onChange(next);
  }

  return (
    <div className="flex flex-col gap-space-md">
      <div className="flex items-center justify-between gap-space-sm">
        <div>
          <h2 className="text-headline-sm text-on-surface">Application form</h2>
          <p className="mt-0.5 text-body-sm text-on-surface-variant">
            Email, resume, and consent are always included. Add extra questions if you need them.
          </p>
        </div>
        <div className="flex rounded-lg border border-outline-variant p-0.5">
          <button
            className={cn(
              "rounded-md px-3 py-1 text-label-md",
              tab === "build" ? "bg-surface-container text-on-surface" : "text-on-surface-variant",
            )}
            onClick={() => setTab("build")}
            type="button"
          >
            Build
          </button>
          <button
            className={cn(
              "rounded-md px-3 py-1 text-label-md",
              tab === "preview" ? "bg-surface-container text-on-surface" : "text-on-surface-variant",
            )}
            onClick={() => setTab("preview")}
            type="button"
          >
            Preview
          </button>
        </div>
      </div>

      {error ? <p className="text-body-sm text-error">{error}</p> : null}

      {tab === "preview" ? (
        <div className="flex flex-col gap-space-lg rounded-xl border border-outline-variant bg-surface-container-lowest p-space-lg">
          {fields.length === 0 ? (
            <p className="text-body-md text-on-surface-variant">
              No custom questions. Candidates will only submit email, a resume PDF, and consent.
            </p>
          ) : (
            fields.map((field) => (
              <FormFieldInput
                field={field}
                key={field.id}
                onChange={(value) =>
                  setPreviewValues((current) => ({ ...current, [field.id]: value }))
                }
                value={previewValues[field.id]}
              />
            ))
          )}
        </div>
      ) : (
        <div className="flex flex-col gap-space-sm">
          {LOCKED_ROWS.map((row) => (
            <div
              className="flex items-start gap-space-sm rounded-lg border border-outline-variant bg-surface-container-low px-space-md py-3"
              key={row.title}
            >
              <Icon className="mt-0.5 text-secondary" name={row.icon} />
              <div>
                <p className="text-label-md font-medium text-on-surface">
                  {row.title}{" "}
                  <span className="text-label-sm font-normal text-on-surface-variant">
                    Always included
                  </span>
                </p>
                <p className="text-body-sm text-on-surface-variant">{row.detail}</p>
              </div>
            </div>
          ))}

          {fields.map((field, index) => (
            <FieldCard
              disabled={disabled}
              field={field}
              index={index}
              key={field.id}
              onDelete={() => onChange(fields.filter((item) => item.id !== field.id))}
              onDown={() => moveField(index, 1)}
              onUp={() => moveField(index, -1)}
              onChange={(next) => updateField(field.id, next)}
              total={fields.length}
            />
          ))}

          {!disabled ? (
            <div className="flex flex-wrap gap-2 pt-1">
              {FORM_FIELD_TYPES.map((item) => {
                const fileBlocked = item.type === "file" && fileCount >= MAX_FILE_FIELDS;
                return (
                  <button
                    className="inline-flex items-center gap-1 rounded-lg border border-outline-variant bg-surface-container-lowest px-3 py-1.5 text-label-md text-on-surface hover:border-secondary disabled:opacity-50"
                    disabled={atFieldCap || fileBlocked}
                    key={item.type}
                    onClick={() => addField(item.type)}
                    type="button"
                  >
                    <Icon className="text-[16px]" name={item.icon} />
                    {item.label}
                  </button>
                );
              })}
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

function FieldCard({
  field,
  index,
  total,
  disabled,
  onChange,
  onDelete,
  onUp,
  onDown,
}: {
  field: FormField;
  index: number;
  total: number;
  disabled: boolean;
  onChange: (field: FormField) => void;
  onDelete: () => void;
  onUp: () => void;
  onDown: () => void;
}) {
  const typeLabel = FORM_FIELD_TYPES.find((item) => item.type === field.type)?.label ?? field.type;

  return (
    <article className="rounded-xl border border-outline-variant bg-surface-container-lowest p-space-md">
      <div className="mb-space-sm flex items-center justify-between gap-space-sm">
        <p className="text-label-sm font-semibold tracking-wider text-secondary uppercase">
          {typeLabel}
        </p>
        <div className="flex items-center gap-1">
          <button
            aria-label="Move up"
            className="rounded p-1 text-on-surface-variant hover:bg-surface-container disabled:opacity-40"
            disabled={disabled || index === 0}
            onClick={onUp}
            type="button"
          >
            <Icon className="text-[18px]" name="arrow_upward" />
          </button>
          <button
            aria-label="Move down"
            className="rounded p-1 text-on-surface-variant hover:bg-surface-container disabled:opacity-40"
            disabled={disabled || index === total - 1}
            onClick={onDown}
            type="button"
          >
            <Icon className="text-[18px]" name="arrow_downward" />
          </button>
          <button
            aria-label="Delete field"
            className="rounded p-1 text-on-surface-variant hover:bg-surface-container hover:text-error disabled:opacity-40"
            disabled={disabled}
            onClick={onDelete}
            type="button"
          >
            <Icon className="text-[18px]" name="delete" />
          </button>
        </div>
      </div>

      <div className="flex flex-col gap-space-sm">
        <Input
          disabled={disabled}
          id={`${field.id}-label`}
          label="Label"
          onChange={(event) => onChange({ ...field, label: event.target.value })}
          required
          type="text"
          value={field.label}
        />
        <Input
          disabled={disabled}
          id={`${field.id}-help`}
          label="Help text"
          onChange={(event) => onChange({ ...field, help_text: event.target.value })}
          type="text"
          value={field.help_text ?? ""}
        />
        <label className="flex cursor-pointer items-center gap-space-sm">
          <input
            checked={field.required}
            className="size-4 rounded border-outline"
            disabled={disabled}
            onChange={(event) => onChange({ ...field, required: event.target.checked })}
            type="checkbox"
          />
          <span className="text-label-md text-on-surface">Required</span>
        </label>

        {field.type === "text" ? (
          <>
            <label className="flex cursor-pointer items-center gap-space-sm">
              <input
                checked={field.multiline}
                className="size-4 rounded border-outline"
                disabled={disabled}
                onChange={(event) => onChange({ ...field, multiline: event.target.checked })}
                type="checkbox"
              />
              <span className="text-label-md text-on-surface">Long text</span>
            </label>
            <Input
              disabled={disabled}
              id={`${field.id}-max`}
              label="Max characters"
              min={1}
              onChange={(event) =>
                onChange({ ...field, max_length: Number(event.target.value) || 1 })
              }
              type="number"
              value={field.max_length}
            />
          </>
        ) : null}

        {field.type === "number" ? (
          <div className="grid grid-cols-2 gap-space-sm">
            <Input
              disabled={disabled}
              id={`${field.id}-min`}
              label="Min"
              onChange={(event) =>
                onChange({
                  ...field,
                  min: event.target.value === "" ? null : Number(event.target.value),
                })
              }
              type="number"
              value={field.min ?? ""}
            />
            <Input
              disabled={disabled}
              id={`${field.id}-max`}
              label="Max"
              onChange={(event) =>
                onChange({
                  ...field,
                  max: event.target.value === "" ? null : Number(event.target.value),
                })
              }
              type="number"
              value={field.max ?? ""}
            />
            <label className="col-span-2 flex cursor-pointer items-center gap-space-sm">
              <input
                checked={field.integer_only}
                className="size-4 rounded border-outline"
                disabled={disabled}
                onChange={(event) => onChange({ ...field, integer_only: event.target.checked })}
                type="checkbox"
              />
              <span className="text-label-md text-on-surface">Whole numbers only</span>
            </label>
          </div>
        ) : null}

        {field.type === "dropdown" || field.type === "radio" || field.type === "checkboxes" ? (
          <OptionsEditor
            disabled={disabled}
            onChange={(options) => onChange({ ...field, options })}
            options={field.options}
          />
        ) : null}

        {field.type === "file" ? (
          <fieldset>
            <legend className="mb-1.5 text-label-md font-medium text-on-surface">
              Allowed types
            </legend>
            <div className="flex flex-wrap gap-space-sm">
              {FILE_ACCEPTS.map((item) => {
                const checked = field.accept.includes(item);
                return (
                  <label className="flex cursor-pointer items-center gap-1.5" key={item}>
                    <input
                      checked={checked}
                      className="size-4 rounded border-outline"
                      disabled={disabled}
                      onChange={() => {
                        const next = checked
                          ? field.accept.filter((value) => value !== item)
                          : [...field.accept, item];
                        onChange({ ...field, accept: next.length > 0 ? next : [item] });
                      }}
                      type="checkbox"
                    />
                    <span className="text-label-md text-on-surface">{FILE_ACCEPT_LABEL[item]}</span>
                  </label>
                );
              })}
            </div>
          </fieldset>
        ) : null}
      </div>
    </article>
  );
}

function OptionsEditor({
  options,
  disabled,
  onChange,
}: {
  options: string[];
  disabled: boolean;
  onChange: (options: string[]) => void;
}) {
  return (
    <div className="flex flex-col gap-2">
      <p className="text-label-md font-medium text-on-surface">Options</p>
      {options.map((option, index) => (
        <div className="flex items-center gap-2" key={`${index}`}>
          <input
            className="w-full rounded-md border border-outline-variant bg-surface-container-lowest px-3 py-2 text-body-md text-on-surface outline-none focus:border-secondary"
            disabled={disabled}
            onChange={(event) => {
              const next = [...options];
              next[index] = event.target.value;
              onChange(next);
            }}
            value={option}
          />
          <button
            aria-label="Remove option"
            className="rounded p-1 text-on-surface-variant hover:text-error disabled:opacity-40"
            disabled={disabled || options.length <= 2}
            onClick={() => onChange(options.filter((_, itemIndex) => itemIndex !== index))}
            type="button"
          >
            <Icon className="text-[18px]" name="close" />
          </button>
        </div>
      ))}
      <button
        className="self-start text-label-md text-secondary hover:underline disabled:opacity-40"
        disabled={disabled || options.length >= 50}
        onClick={() => onChange([...options, `Option ${options.length + 1}`])}
        type="button"
      >
        Add option
      </button>
    </div>
  );
}
