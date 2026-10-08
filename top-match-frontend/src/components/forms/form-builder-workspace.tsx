"use client";

import type { ReactNode } from "react";

import { ConditionBuilder } from "@/components/forms/condition-builder";
import {
  FieldNotices,
  inputClass,
  numberOrNull,
  ReasonInput,
  smallInputClass,
  Switch,
  WeightInput,
} from "@/components/forms/form-builder-controls";
import { Icon } from "@/components/icon";
import { cn } from "@/lib/cn";
import { isConditionField, type ConditionField } from "@/lib/condition-presets";
import {
  FILE_ACCEPT_LABEL,
  FORM_FIELD_TYPES,
  MAX_CONDITIONS,
  MAX_FILE_FIELDS,
  MAX_FORM_FIELDS,
  newFormField,
  newYesNoKnockout,
  type ChoiceFormField,
  type FileAccept,
  type FormField,
  type FormFieldType,
  type FormWarning,
  type GuardrailError,
  type NumberFormField,
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

type FormBuilderWorkspaceProps = {
  fields: FormField[];
  onChange: (fields: FormField[]) => void;
  disabled?: boolean;
  error?: string;
  // Warnings from the last save (age proxies, salary history). They never block saving.
  warnings?: FormWarning[];
  // Guardrail errors from the last save attempt, keyed by field id.
  blocked?: GuardrailError[];
};

/** Keep knockout and scoring config in step with the field's options. */
function withOptions(field: ChoiceFormField, options: string[]): ChoiceFormField {
  const next: ChoiceFormField = { ...field, options };
  if (field.knockout) {
    next.knockout = {
      ...field.knockout,
      allowed_values: field.knockout.allowed_values.filter((value) => options.includes(value)),
    };
  }
  if (field.scoring) {
    next.scoring = {
      ...field.scoring,
      option_scores: Object.fromEntries(
        Object.entries(field.scoring.option_scores).filter(([option]) => options.includes(option)),
      ),
    };
  }
  return next;
}

export function FormBuilderWorkspace({
  fields,
  onChange,
  disabled = false,
  error,
  warnings = [],
  blocked = [],
}: FormBuilderWorkspaceProps) {
  // Conditions come first on the apply form; questions follow in their own order.
  const conditions = fields.filter(isConditionField);
  const questions = fields.filter((field) => !isConditionField(field));
  const fileCount = questions.filter((field) => field.type === "file").length;
  const atFieldCap = questions.length >= MAX_FORM_FIELDS;

  function setQuestions(next: FormField[]) {
    onChange([...conditions, ...next]);
  }

  function setConditions(next: ConditionField[]) {
    onChange([...next, ...questions]);
  }

  function updateField(id: string, next: FormField) {
    setQuestions(questions.map((field) => (field.id === id ? next : field)));
  }

  function addField(type: FormFieldType) {
    if (disabled || atFieldCap) {
      return;
    }
    if (type === "file" && fileCount >= MAX_FILE_FIELDS) {
      return;
    }
    setQuestions([...questions, newFormField(type)]);
  }

  function addYesNoKnockout() {
    if (disabled || atFieldCap) {
      return;
    }
    setQuestions([...questions, newYesNoKnockout()]);
  }

  function moveField(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= questions.length) {
      return;
    }
    const next = [...questions];
    const [item] = next.splice(index, 1);
    next.splice(target, 0, item);
    setQuestions(next);
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
            Up to {MAX_CONDITIONS} job conditions and {MAX_FORM_FIELDS} custom questions (max{" "}
            {MAX_FILE_FIELDS} file uploads). Custom answers
            are stored for recruiters and are{" "}
            <strong className="font-semibold text-on-surface">NOT</strong> sent to AI scoring.
            Knockouts and answer weights are checked in code before the resume is scored.
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

      <ConditionBuilder
        blocked={blocked}
        conditions={conditions}
        disabled={disabled}
        onChange={setConditions}
        warnings={warnings}
      />

      <section className="flex flex-col gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h2 className="text-headline-md font-bold text-on-surface">Custom questions</h2>
            <span className="rounded-full border border-secondary-fixed bg-surface-container px-2 py-0.5 text-label-sm font-semibold text-secondary">
              {questions.length} of {MAX_FORM_FIELDS} questions used ({fileCount} of {MAX_FILE_FIELDS}{" "}
              uploads)
            </span>
          </div>
          <p className="mt-0.5 text-body-sm text-on-surface-variant">
            Stored in candidate dossier for recruiter review. Not evaluated by AI scoring.
          </p>
        </div>

        <div className="flex flex-col gap-4">
          {questions.map((field, index) => (
            <WorkspaceFieldCard
              blocked={blocked.filter((item) => item.target === field.id)}
              disabled={disabled}
              field={field}
              fileIndex={
                field.type === "file"
                  ? questions.slice(0, index + 1).filter((item) => item.type === "file").length
                  : 0
              }
              index={index}
              key={field.id}
              onChange={(next) => updateField(field.id, next)}
              onDelete={() => setQuestions(questions.filter((item) => item.id !== field.id))}
              onDown={() => moveField(index, 1)}
              onUp={() => moveField(index, -1)}
              total={questions.length}
              warnings={warnings.filter((warning) => warning.field_id === field.id)}
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
            <button
              className="inline-flex items-center gap-1.5 rounded-lg border border-outline-variant bg-surface-container-lowest px-3 py-1.5 text-label-md text-on-surface transition-all hover:border-secondary hover:bg-surface-container-low disabled:opacity-50"
              disabled={atFieldCap}
              onClick={addYesNoKnockout}
              type="button"
            >
              <Icon className="text-[17px] text-secondary" name="filter_alt" />+ Yes/no knockout
            </button>
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
  warnings,
  blocked,
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
  warnings: FormWarning[];
  blocked: GuardrailError[];
}) {
  const isKnockout =
    (field.type === "number" || field.type === "dropdown" || field.type === "radio") &&
    Boolean(field.knockout);
  return (
    <article className="min-w-0 overflow-hidden rounded-xl border border-outline-variant bg-surface-container-lowest p-4 shadow-sm transition-all hover:border-secondary">
      <div className="flex items-center justify-between border-b border-surface-container-high pb-3">
        <div className="flex items-center gap-2">
          <span className="rounded border border-secondary-fixed bg-surface-container-low px-2 py-0.5 text-label-sm font-semibold tracking-wide text-secondary uppercase">
            {TYPE_BADGE[field.type]}
          </span>
          {isKnockout ? (
            <span className="rounded border border-status-knocked-out/30 bg-status-knocked-out-container px-2 py-0.5 text-label-sm font-semibold text-status-knocked-out uppercase">
              Knockout
            </span>
          ) : null}
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
            disabled={disabled || isKnockout}
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
                      onChange(withOptions(field, next));
                    }}
                    type="text"
                    value={option}
                  />
                  <button
                    aria-label="Remove option"
                    className="p-1 text-on-surface-variant hover:text-error disabled:opacity-40"
                    disabled={disabled || field.options.length <= 2}
                    onClick={() =>
                      onChange(
                        withOptions(
                          field,
                          field.options.filter((_, itemIndex) => itemIndex !== optionIndex),
                        ),
                      )
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
                onChange(withOptions(field, [...field.options, `Option ${field.options.length + 1}`]))
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
              disabled={disabled || isKnockout}
              label="Required field"
              onChange={(required) => onChange({ ...field, required })}
            />
          </div>
        </>
      ) : null}

      {field.type === "number" ? (
        <>
          <NumberKnockoutEditor disabled={disabled} field={field} onChange={onChange} />
          <NumberScoringEditor disabled={disabled} field={field} onChange={onChange} />
        </>
      ) : null}

      {field.type === "dropdown" || field.type === "radio" ? (
        <ChoiceKnockoutEditor disabled={disabled} field={field} onChange={onChange} />
      ) : null}

      {field.type === "dropdown" || field.type === "radio" || field.type === "checkboxes" ? (
        <ChoiceScoringEditor disabled={disabled} field={field} onChange={onChange} />
      ) : null}

      <FieldNotices blocked={blocked} warnings={warnings} />

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

function ConfigSection({
  title,
  enabled,
  disabled,
  onToggle,
  hint,
  children,
}: {
  title: string;
  enabled: boolean;
  disabled: boolean;
  onToggle: (enabled: boolean) => void;
  hint: string;
  children: ReactNode;
}) {
  return (
    <div className="mt-3.5 border-t border-surface-container pt-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Switch checked={enabled} disabled={disabled} label={title} onChange={onToggle} />
        <span className="text-body-sm text-on-surface-variant">{hint}</span>
      </div>
      {enabled ? <div className="mt-2.5 flex flex-col gap-2.5">{children}</div> : null}
    </div>
  );
}

function ChoiceKnockoutEditor({
  field,
  disabled,
  onChange,
}: {
  field: ChoiceFormField;
  disabled: boolean;
  onChange: (field: FormField) => void;
}) {
  const knockout = field.knockout;
  return (
    <ConfigSection
      disabled={disabled}
      enabled={Boolean(knockout)}
      hint="Checked in code. Failing applicants skip resume scoring."
      onToggle={(enabled) =>
        onChange(
          enabled
            ? { ...field, required: true, knockout: { reason: "", allowed_values: [field.options[0]] } }
            : { ...field, knockout: null },
        )
      }
      title="Knockout question"
    >
      {knockout ? (
        <>
          <div>
            <p className="mb-1 text-label-sm font-semibold text-on-surface">Answers that pass</p>
            <div className="flex flex-wrap gap-2">
              {field.options.map((option) => {
                const checked = knockout.allowed_values.includes(option);
                return (
                  <label
                    className="inline-flex cursor-pointer items-center gap-1.5 text-label-sm text-on-surface"
                    key={option}
                  >
                    <input
                      checked={checked}
                      className="size-3.5 rounded border-outline-variant"
                      disabled={disabled}
                      onChange={() =>
                        onChange({
                          ...field,
                          knockout: {
                            ...knockout,
                            allowed_values: checked
                              ? knockout.allowed_values.filter((value) => value !== option)
                              : [...knockout.allowed_values, option],
                          },
                        })
                      }
                      type="checkbox"
                    />
                    {option}
                  </label>
                );
              })}
            </div>
          </div>
          <ReasonInput
            disabled={disabled}
            onChange={(reason) => onChange({ ...field, knockout: { ...knockout, reason } })}
            value={knockout.reason}
          />
        </>
      ) : null}
    </ConfigSection>
  );
}

function NumberKnockoutEditor({
  field,
  disabled,
  onChange,
}: {
  field: NumberFormField;
  disabled: boolean;
  onChange: (field: FormField) => void;
}) {
  const knockout = field.knockout;
  return (
    <ConfigSection
      disabled={disabled}
      enabled={Boolean(knockout)}
      hint="Applicants below the minimum can still apply; they are knocked out."
      onToggle={(enabled) =>
        onChange(
          enabled
            ? { ...field, required: true, knockout: { reason: "", min: field.min ?? 0 } }
            : { ...field, knockout: null },
        )
      }
      title="Knockout question"
    >
      {knockout ? (
        <>
          <label className="flex items-center gap-1.5 text-label-sm text-on-surface">
            Minimum to pass:
            <input
              className={smallInputClass}
              disabled={disabled}
              onChange={(event) =>
                onChange({
                  ...field,
                  knockout: { ...knockout, min: numberOrNull(event.target.value) ?? 0 },
                })
              }
              type="number"
              value={knockout.min ?? ""}
            />
          </label>
          <ReasonInput
            disabled={disabled}
            onChange={(reason) => onChange({ ...field, knockout: { ...knockout, reason } })}
            value={knockout.reason}
          />
        </>
      ) : null}
    </ConfigSection>
  );
}

function ChoiceScoringEditor({
  field,
  disabled,
  onChange,
}: {
  field: ChoiceFormField;
  disabled: boolean;
  onChange: (field: FormField) => void;
}) {
  const scoring = field.scoring;
  return (
    <ConfigSection
      disabled={disabled}
      enabled={Boolean(scoring)}
      hint="Adds to the answers score. Never sent to the model."
      onToggle={(enabled) =>
        onChange(
          enabled
            ? { ...field, scoring: { weight: 1, option_scores: {} } }
            : { ...field, scoring: null },
        )
      }
      title="Score this answer"
    >
      {scoring ? (
        <>
          <WeightInput
            disabled={disabled}
            onChange={(weight) => onChange({ ...field, scoring: { ...scoring, weight } })}
            weight={scoring.weight}
          />
          <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
            {field.options.map((option) => (
              <label
                className="flex items-center justify-between gap-2 text-label-sm text-on-surface"
                key={option}
              >
                <span className="truncate">{option}</span>
                <input
                  className={smallInputClass}
                  disabled={disabled}
                  max={1}
                  min={0}
                  onChange={(event) => {
                    const value = numberOrNull(event.target.value);
                    const optionScores = { ...scoring.option_scores };
                    if (value === null) {
                      delete optionScores[option];
                    } else {
                      optionScores[option] = Math.min(1, Math.max(0, value));
                    }
                    onChange({ ...field, scoring: { ...scoring, option_scores: optionScores } });
                  }}
                  placeholder="0"
                  step={0.25}
                  type="number"
                  value={scoring.option_scores[option] ?? ""}
                />
              </label>
            ))}
          </div>
          <p className="text-body-sm text-on-surface-variant">
            Points per option, from 0 to 1.
            {field.type === "checkboxes" ? " Selected options add up, capped at 1." : null}
          </p>
        </>
      ) : null}
    </ConfigSection>
  );
}

function NumberScoringEditor({
  field,
  disabled,
  onChange,
}: {
  field: NumberFormField;
  disabled: boolean;
  onChange: (field: FormField) => void;
}) {
  const scoring = field.scoring;
  return (
    <ConfigSection
      disabled={disabled}
      enabled={Boolean(scoring)}
      hint="Adds to the answers score. Never sent to the model."
      onToggle={(enabled) =>
        onChange(
          enabled ? { ...field, scoring: { weight: 1, target: 1 } } : { ...field, scoring: null },
        )
      }
      title="Score this answer"
    >
      {scoring ? (
        <div className="flex flex-wrap items-center gap-4">
          <WeightInput
            disabled={disabled}
            onChange={(weight) => onChange({ ...field, scoring: { ...scoring, weight } })}
            weight={scoring.weight}
          />
          <label className="flex items-center gap-1.5 text-label-sm text-on-surface">
            Full points at:
            <input
              className={smallInputClass}
              disabled={disabled}
              min={0}
              onChange={(event) =>
                onChange({
                  ...field,
                  scoring: { ...scoring, target: numberOrNull(event.target.value) ?? 0 },
                })
              }
              type="number"
              value={scoring.target}
            />
          </label>
        </div>
      ) : null}
    </ConfigSection>
  );
}
