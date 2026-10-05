"use client";

import { Icon } from "@/components/icon";
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

const TYPE_BADGE: Record<FormFieldType, string> = {
  text: "Text field",
  number: "Number field",
  dropdown: "Dropdown field",
  radio: "Single choice",
  checkboxes: "Multiple choice",
  file: "File upload (extra)",
};

const LOCKED_ROWS = [
  {
    icon: "mail",
    title: "Email address",
    detail: "Unique identifier, prevents duplicate submissions. Always required.",
    chip: "Always included · Locked",
    scored: false,
  },
  {
    icon: "picture_as_pdf",
    title: "Resume PDF (max 5 MB)",
    detail: "The ONLY file parsed and sent to AI evaluation rubric. Always required.",
    chip: "Always included · Scored by AI",
    scored: true,
  },
  {
    icon: "verified_user",
    title: "Consent checkbox",
    detail: "Mandatory privacy and AI screening transparency statement. Always required.",
    chip: "Always included · Legal",
    scored: false,
  },
] as const;

const inputClass =
  "w-full min-w-0 max-w-full rounded-lg border border-outline-variant bg-surface-container-lowest px-3 py-1.5 text-body-md text-on-surface outline-none focus:border-secondary focus:ring-2 focus:ring-secondary/20 disabled:opacity-60";

type FormBuilderWorkspaceProps = {
  fields: FormField[];
  onChange: (fields: FormField[]) => void;
  disabled?: boolean;
  error?: string;
};

export function FormBuilderWorkspace({
  fields,
  onChange,
  disabled = false,
  error,
}: FormBuilderWorkspaceProps) {
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
    <div className="flex min-w-0 max-w-full flex-col gap-6">
      <div>
        <h1 className="text-headline-lg font-bold tracking-tight text-on-surface">Application form</h1>
        <p className="mt-1 text-body-md text-on-surface-variant">
          Email, resume, and consent are always included. Add extra questions if this role needs them.
        </p>
        <div className="mt-3.5 flex items-start gap-2.5 rounded-lg border border-secondary-fixed bg-surface-container-low p-3 text-label-md text-on-secondary-container">
          <Icon className="mt-0.5 shrink-0 text-[18px] text-secondary" name="info" />
          <p>
            <span className="font-semibold text-secondary">Builder Constraints: </span>
            Up to {MAX_FORM_FIELDS} custom fields (max {MAX_FILE_FIELDS} file uploads). Custom answers
            are stored for recruiters and are{" "}
            <strong className="font-semibold text-on-surface">NOT</strong> sent to AI scoring.
          </p>
        </div>
      </div>

      {error ? <p className="text-body-sm text-error">{error}</p> : null}

      <section className="overflow-hidden rounded-xl border border-outline-variant bg-surface-container-lowest shadow-sm">
        <div className="flex items-center justify-between border-b border-outline-variant bg-surface-container-low px-5 py-3.5">
          <div className="flex items-center gap-2">
            <Icon className="text-[18px] text-on-surface-variant" name="lock" />
            <span className="text-label-sm font-bold tracking-wider text-on-surface uppercase">
              Always Included (Mandatory)
            </span>
          </div>
          <span className="text-label-sm text-on-surface-variant">3 non-configurable system fields</span>
        </div>
        <div className="space-y-2.5 p-4">
          <p className="mb-2 text-body-sm text-on-surface-variant">
            These 3 fields are non-removable, non-reorderable, and satisfy institutional compliance.
          </p>
          {LOCKED_ROWS.map((row) => (
            <div
              className="flex flex-col gap-3 rounded-lg border border-outline-variant bg-surface-bright p-3 sm:flex-row sm:items-center sm:justify-between"
              key={row.title}
            >
              <div className="flex items-center gap-3">
                <div className="flex size-8 items-center justify-center rounded-md bg-surface-container text-secondary">
                  <Icon className="text-[18px]" name={row.icon} />
                </div>
                <div>
                  <p className="flex items-center gap-2 text-headline-sm font-semibold text-on-surface">
                    {row.title}
                    <span className="text-body-sm text-error">*</span>
                  </p>
                  <p className="text-body-sm text-on-surface-variant">{row.detail}</p>
                </div>
              </div>
              <span
                className={cn(
                  "shrink-0 rounded px-2.5 py-1 text-label-sm font-medium",
                  row.scored
                    ? "flex items-center gap-1 border border-secondary-container bg-secondary-fixed text-on-secondary-fixed-variant"
                    : "border border-outline-variant bg-surface-container text-on-secondary-container",
                )}
              >
                {row.scored ? <span className="size-1.5 rounded-full bg-secondary" /> : null}
                {row.chip}
              </span>
            </div>
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h2 className="text-headline-md font-bold text-on-surface">Custom questions</h2>
            <span className="rounded-full border border-secondary-fixed bg-surface-container px-2 py-0.5 text-label-sm font-semibold text-secondary">
              {fields.length} of {MAX_FORM_FIELDS} fields used ({fileCount} of {MAX_FILE_FIELDS}{" "}
              uploads)
            </span>
          </div>
          <p className="mt-0.5 text-body-sm text-on-surface-variant">
            Stored in candidate dossier for recruiter review. Not evaluated by AI scoring.
          </p>
        </div>

        <div className="flex flex-col gap-4">
          {fields.map((field, index) => (
            <WorkspaceFieldCard
              disabled={disabled}
              field={field}
              fileIndex={
                field.type === "file"
                  ? fields.slice(0, index + 1).filter((item) => item.type === "file").length
                  : 0
              }
              index={index}
              key={field.id}
              onChange={(next) => updateField(field.id, next)}
              onDelete={() => onChange(fields.filter((item) => item.id !== field.id))}
              onDown={() => moveField(index, 1)}
              onUp={() => moveField(index, -1)}
              total={fields.length}
            />
          ))}
        </div>
      </section>

      {!disabled ? (
        <section className="rounded-xl border border-dashed border-outline-variant bg-surface-bright p-4">
          <p className="mb-2.5 flex items-center gap-1.5 text-label-sm font-bold tracking-wider text-on-surface uppercase">
            <Icon className="text-[16px] text-secondary" name="add_circle" />
            Add another question
          </p>
          <div className="flex flex-wrap gap-2">
            {FORM_FIELD_TYPES.map((item) => {
              const fileBlocked = item.type === "file" && fileCount >= MAX_FILE_FIELDS;
              return (
                <button
                  className="inline-flex items-center gap-1.5 rounded-lg border border-outline-variant bg-surface-container-lowest px-3 py-1.5 text-label-md text-on-surface transition-all hover:border-secondary hover:bg-surface-container-low disabled:opacity-50"
                  disabled={atFieldCap || fileBlocked}
                  key={item.type}
                  onClick={() => addField(item.type)}
                  type="button"
                >
                  <Icon className="text-[17px] text-secondary" name={item.icon} />+ {item.label}
                </button>
              );
            })}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function WorkspaceFieldCard({
  field,
  index,
  total,
  fileIndex,
  disabled,
  onChange,
  onDelete,
  onUp,
  onDown,
}: {
  field: FormField;
  index: number;
  total: number;
  fileIndex: number;
  disabled: boolean;
  onChange: (field: FormField) => void;
  onDelete: () => void;
  onUp: () => void;
  onDown: () => void;
}) {
  return (
    <article className="min-w-0 overflow-hidden rounded-xl border border-outline-variant bg-surface-container-lowest p-4 shadow-sm transition-all hover:border-secondary">
      <div className="flex items-center justify-between border-b border-surface-container-high pb-3">
        <div className="flex items-center gap-2">
          <span className="rounded border border-secondary-fixed bg-surface-container-low px-2 py-0.5 text-label-sm font-semibold tracking-wide text-secondary uppercase">
            {TYPE_BADGE[field.type]}
          </span>
          <span className="text-label-sm text-on-surface-variant">
            Position {index + 1}
            {field.type === "file" ? ` · ${fileIndex} of ${MAX_FILE_FIELDS} allowed uploads` : ""}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            aria-label="Move up"
            className="rounded p-1 text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface disabled:opacity-40"
            disabled={disabled || index === 0}
            onClick={onUp}
            type="button"
          >
            <Icon className="text-[18px]" name="arrow_upward" />
          </button>
          <button
            aria-label="Move down"
            className="rounded p-1 text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface disabled:opacity-40"
            disabled={disabled || index === total - 1}
            onClick={onDown}
            type="button"
          >
            <Icon className="text-[18px]" name="arrow_downward" />
          </button>
          <div className="mx-1 h-3 w-px bg-outline-variant" />
          <button
            aria-label="Delete question"
            className="rounded p-1 text-on-surface-variant hover:bg-error-container/40 hover:text-error disabled:opacity-40"
            disabled={disabled}
            onClick={onDelete}
            type="button"
          >
            <Icon className="text-[18px]" name="delete_outline" />
          </button>
        </div>
      </div>

      <div className="mt-3.5 grid min-w-0 grid-cols-1 gap-3.5 md:grid-cols-2">
        <label className="block min-w-0">
          <span className="mb-1 block text-label-sm font-semibold text-on-surface">Field Label</span>
          <input
            className={inputClass}
            disabled={disabled}
            onChange={(event) => onChange({ ...field, label: event.target.value })}
            type="text"
            value={field.label}
          />
        </label>
        <label className="block min-w-0">
          <span className="mb-1 block text-label-sm font-semibold text-on-surface">Help Text</span>
          <input
            className={inputClass}
            disabled={disabled}
            onChange={(event) => onChange({ ...field, help_text: event.target.value })}
            type="text"
            value={field.help_text ?? ""}
          />
        </label>
      </div>

      {field.type === "text" ? (
        <div className="mt-3.5 flex flex-wrap items-center justify-between gap-3 border-t border-surface-container pt-3">
          <div className="flex flex-wrap items-center gap-5">
            <Switch
              checked={field.required}
              disabled={disabled}
              label="Required field"
              onChange={(required) => onChange({ ...field, required })}
            />
            <Switch
              checked={field.multiline}
              disabled={disabled}
              label="Long text (textarea)"
              onChange={(multiline) => onChange({ ...field, multiline })}
            />
          </div>
          <label className="flex items-center gap-1.5 text-label-sm text-on-surface-variant">
            Max characters:
            <input
              className="w-16 rounded border border-outline-variant px-1.5 py-0.5 text-center font-mono text-xs disabled:opacity-60"
              disabled={disabled}
              min={1}
              onChange={(event) =>
                onChange({ ...field, max_length: Number(event.target.value) || 1 })
              }
              type="number"
              value={field.max_length}
            />
          </label>
        </div>
      ) : null}

      {field.type === "number" ? (
        <div className="mt-3.5 flex flex-wrap items-center justify-between gap-3 border-t border-surface-container pt-3">
          <div className="flex flex-wrap items-center gap-4">
            <label className="flex items-center gap-1.5 text-label-sm text-on-surface">
              Min:
              <input
                className="w-14 rounded border border-outline-variant px-1.5 py-0.5 text-center font-mono text-xs disabled:opacity-60"
                disabled={disabled}
                onChange={(event) =>
                  onChange({
                    ...field,
                    min: event.target.value === "" ? null : Number(event.target.value),
                  })
                }
                type="number"
                value={field.min ?? ""}
              />
            </label>
            <label className="flex items-center gap-1.5 text-label-sm text-on-surface">
              Max:
              <input
                className="w-14 rounded border border-outline-variant px-1.5 py-0.5 text-center font-mono text-xs disabled:opacity-60"
                disabled={disabled}
                onChange={(event) =>
                  onChange({
                    ...field,
                    max: event.target.value === "" ? null : Number(event.target.value),
                  })
                }
                type="number"
                value={field.max ?? ""}
              />
            </label>
            <label className="flex cursor-pointer items-center gap-1.5 text-label-sm text-on-surface">
              <input
                checked={field.integer_only}
                className="size-3.5 rounded border-outline-variant"
                disabled={disabled}
                onChange={(event) => onChange({ ...field, integer_only: event.target.checked })}
                type="checkbox"
              />
              Whole numbers only
            </label>
          </div>
          <Switch
            checked={field.required}
            disabled={disabled}
            label="Required field"
            onChange={(required) => onChange({ ...field, required })}
          />
        </div>
      ) : null}

      {field.type === "dropdown" || field.type === "radio" || field.type === "checkboxes" ? (
        <>
          <div className="mt-3.5">
            <p className="mb-1.5 text-label-sm font-semibold text-on-surface">
              {field.type === "dropdown" ? "Dropdown Options" : "Options"}
            </p>
            <div className="space-y-1.5">
              {field.options.map((option, optionIndex) => (
                <div className="flex items-center gap-2" key={`${field.id}-${optionIndex}`}>
                  <input
                    className="flex-1 rounded border border-outline-variant bg-surface-bright px-2.5 py-1 text-body-sm text-on-surface outline-none focus:border-secondary disabled:opacity-60"
                    disabled={disabled}
                    onChange={(event) => {
                      const next = [...field.options];
                      next[optionIndex] = event.target.value;
                      onChange({ ...field, options: next });
                    }}
                    type="text"
                    value={option}
                  />
                  <button
                    aria-label="Remove option"
                    className="p-1 text-on-surface-variant hover:text-error disabled:opacity-40"
                    disabled={disabled || field.options.length <= 2}
                    onClick={() =>
                      onChange({
                        ...field,
                        options: field.options.filter((_, itemIndex) => itemIndex !== optionIndex),
                      })
                    }
                    type="button"
                  >
                    <Icon className="text-[16px]" name="close" />
                  </button>
                </div>
              ))}
            </div>
            <button
              className="mt-2 inline-flex items-center gap-1.5 rounded border border-dashed border-outline-variant px-2.5 py-1 text-label-sm text-secondary hover:border-secondary hover:bg-surface-container-low disabled:opacity-40"
              disabled={disabled || field.options.length >= 50}
              onClick={() =>
                onChange({ ...field, options: [...field.options, `Option ${field.options.length + 1}`] })
              }
              type="button"
            >
              <Icon className="text-[16px]" name="add" />
              Add option
            </button>
          </div>
          <div className="mt-3.5 flex items-center justify-between border-t border-surface-container pt-3">
            <span className="text-body-sm text-on-surface-variant">
              {field.type === "checkboxes"
                ? "Candidates can select more than one option."
                : "Candidates can select exactly one option from the menu."}
            </span>
            <Switch
              checked={field.required}
              disabled={disabled}
              label="Required field"
              onChange={(required) => onChange({ ...field, required })}
            />
          </div>
        </>
      ) : null}

      {field.type === "file" ? (
        <>
          <div className="mt-3.5">
            <p className="mb-1.5 text-label-sm font-semibold text-on-surface">Allowed File Types</p>
            <div className="flex flex-wrap items-center gap-2">
              {FILE_ACCEPTS.map((item) => {
                const checked = field.accept.includes(item);
                return (
                  <label
                    className={cn(
                      "inline-flex cursor-pointer items-center gap-1.5 rounded border px-2.5 py-1 text-label-sm",
                      checked
                        ? "border-secondary bg-secondary-fixed text-on-secondary-fixed-variant"
                        : "border-outline-variant bg-surface-bright text-on-surface-variant",
                    )}
                    key={item}
                  >
                    <input
                      checked={checked}
                      className="size-3.5 rounded border-outline-variant"
                      disabled={disabled}
                      onChange={() => {
                        const next = checked
                          ? field.accept.filter((value) => value !== item)
                          : [...field.accept, item];
                        onChange({ ...field, accept: next.length > 0 ? next : [item] });
                      }}
                      type="checkbox"
                    />
                    {FILE_ACCEPT_LABEL[item]}
                    {item === "jpeg" ? " (.jpg, .jpeg)" : ` (.${item})`}
                  </label>
                );
              })}
            </div>
          </div>
          <div className="mt-3.5 flex flex-wrap items-center justify-between gap-3 border-t border-surface-container pt-3">
            <span className="rounded bg-surface-container px-2 py-0.5 text-label-sm text-on-secondary-container">
              Max 5 MB · Stored in dossier only
            </span>
            <Switch
              checked={field.required}
              disabled={disabled}
              label="Required field"
              onChange={(required) => onChange({ ...field, required })}
            />
          </div>
        </>
      ) : null}
    </article>
  );
}

function Switch({
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
