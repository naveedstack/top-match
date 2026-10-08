"use client";

import { useState } from "react";

import {
  FieldNotices,
  inputClass,
  numberOrNull,
  ReasonInput,
  smallInputClass,
  WeightInput,
} from "@/components/forms/form-builder-controls";
import { Icon } from "@/components/icon";
import { cn } from "@/lib/cn";
import {
  CONDITION_PRESETS,
  IMPORTANCE_HINT,
  IMPORTANCE_LABEL,
  ORDERED_SCALES,
  PRESET_ORDER,
  newConditionField,
  passingAnswers,
  thresholdOf,
  withImportance,
  withPassing,
  withSalary,
  withReason,
  withThreshold,
  withWeight,
  type ConditionField,
} from "@/lib/condition-presets";
import {
  MAX_CONDITIONS,
  type ConditionImportance,
  type ConditionPreset,
  type FormWarning,
  type GuardrailError,
} from "@/types/forms";

const IMPORTANCES: ConditionImportance[] = ["must", "preferred", "info"];

type ConditionBuilderProps = {
  conditions: ConditionField[];
  onChange: (conditions: ConditionField[]) => void;
  disabled: boolean;
  warnings: FormWarning[];
  blocked: GuardrailError[];
};

export function ConditionBuilder({
  conditions,
  onChange,
  disabled,
  warnings,
  blocked,
}: ConditionBuilderProps) {
  const atCap = conditions.length >= MAX_CONDITIONS;

  function update(id: string, next: ConditionField) {
    onChange(conditions.map((item) => (item.id === id ? next : item)));
  }

  return (
    <section className="flex flex-col gap-4">
      <div>
        <div className="flex items-center gap-2.5">
          <h2 className="text-headline-md font-bold text-on-surface">Job conditions</h2>
          <span className="rounded-full border border-secondary-fixed bg-surface-container px-2 py-0.5 text-label-sm font-semibold text-secondary">
            {conditions.length} of {MAX_CONDITIONS} conditions used
          </span>
        </div>
        <p className="mt-0.5 text-body-sm text-on-surface-variant">
          Non-technical requirements the candidate answers on the form. Checked in code, never
          inferred from the resume. Must conditions are listed under &ldquo;Before you apply&rdquo;.
        </p>
      </div>

      {conditions.map((field) => (
        <ConditionCard
          blocked={blocked.filter((item) => item.target === field.id)}
          disabled={disabled}
          field={field}
          key={field.id}
          onChange={(next) => update(field.id, next)}
          onDelete={() => onChange(conditions.filter((item) => item.id !== field.id))}
          warnings={warnings.filter((item) => item.field_id === field.id)}
        />
      ))}

      {!disabled ? (
        <PresetPicker
          disabled={atCap}
          onAdd={(field) => onChange([...conditions, field])}
        />
      ) : null}
    </section>
  );
}

function PresetPicker({
  disabled,
  onAdd,
}: {
  disabled: boolean;
  onAdd: (field: ConditionField) => void;
}) {
  const [pending, setPending] = useState<ConditionPreset | null>(null);
  const [place, setPlace] = useState("");
  const pendingPlace = pending ? CONDITION_PRESETS[pending].place : undefined;

  function choose(preset: ConditionPreset) {
    if (CONDITION_PRESETS[preset].place) {
      setPending(preset);
      setPlace("");
      return;
    }
    onAdd(newConditionField(preset));
  }

  function addPending() {
    if (pending && place.trim()) {
      onAdd(newConditionField(pending, place));
      setPending(null);
    }
  }

  return (
    <div className="rounded-xl border border-dashed border-outline-variant bg-surface-bright p-4">
      <p className="mb-2.5 flex items-center gap-1.5 text-label-sm font-bold tracking-wider text-on-surface uppercase">
        <Icon className="text-[16px] text-secondary" name="add_circle" />
        Add a job condition
      </p>
      <div className="flex flex-wrap gap-2">
        {PRESET_ORDER.map((preset) => (
          <button
            className={cn(
              "inline-flex items-center gap-1.5 rounded-lg border bg-surface-container-lowest px-3 py-1.5 text-label-md text-on-surface transition-all hover:border-secondary hover:bg-surface-container-low disabled:opacity-50",
              pending === preset ? "border-secondary" : "border-outline-variant",
            )}
            disabled={disabled}
            key={preset}
            onClick={() => choose(preset)}
            type="button"
          >
            <Icon className="text-[17px] text-secondary" name={CONDITION_PRESETS[preset].icon} />+{" "}
            {CONDITION_PRESETS[preset].title}
          </button>
        ))}
      </div>
      {pending && pendingPlace ? (
        <div className="mt-3 flex flex-wrap items-end gap-2">
          <label className="block min-w-0 flex-1">
            <span className="mb-1 block text-label-sm font-semibold text-on-surface">
              {pendingPlace} for {CONDITION_PRESETS[pending].title.toLowerCase()}
            </span>
            <input
              autoFocus
              className={inputClass}
              onChange={(event) => setPlace(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  addPending();
                }
              }}
              placeholder={pendingPlace === "Country" ? "e.g. Pakistan" : "e.g. Lahore"}
              type="text"
              value={place}
            />
          </label>
          <button
            className="rounded-lg bg-secondary px-3 py-1.5 text-label-md text-on-secondary disabled:opacity-50"
            disabled={!place.trim()}
            onClick={addPending}
            type="button"
          >
            Add
          </button>
          <button
            className="rounded-lg border border-outline-variant px-3 py-1.5 text-label-md text-on-surface"
            onClick={() => setPending(null)}
            type="button"
          >
            Cancel
          </button>
        </div>
      ) : null}
    </div>
  );
}

function ConditionCard({
  field,
  disabled,
  onChange,
  onDelete,
  warnings,
  blocked,
}: {
  field: ConditionField;
  disabled: boolean;
  onChange: (field: ConditionField) => void;
  onDelete: () => void;
  warnings: FormWarning[];
  blocked: GuardrailError[];
}) {
  const preset = CONDITION_PRESETS[field.condition.preset];
  const importance = field.condition.importance;
  return (
    <article
      aria-label={`${preset.title} condition`}
      className="min-w-0 overflow-hidden rounded-xl border border-outline-variant bg-surface-container-lowest p-4 shadow-sm transition-all hover:border-secondary"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-surface-container-high pb-3">
        <span className="inline-flex items-center gap-1.5 text-label-md font-semibold text-on-surface">
          <Icon className="text-[18px] text-secondary" name={preset.icon} />
          {preset.title}
        </span>
        <div className="flex items-center gap-2">
          <div aria-label="Importance" className="flex rounded-lg border border-outline-variant p-0.5" role="radiogroup">
            {IMPORTANCES.map((item) => (
              <button
                aria-checked={importance === item}
                className={cn(
                  "rounded-md px-2.5 py-0.5 text-label-sm font-medium",
                  importance === item
                    ? "bg-secondary text-on-secondary"
                    : "text-on-surface-variant hover:bg-surface-container-low",
                )}
                disabled={disabled}
                key={item}
                onClick={() => onChange(withImportance(field, item))}
                role="radio"
                type="button"
              >
                {IMPORTANCE_LABEL[item]}
              </button>
            ))}
          </div>
          <button
            aria-label="Delete condition"
            className="rounded p-1 text-on-surface-variant hover:bg-error-container/40 hover:text-error disabled:opacity-40"
            disabled={disabled}
            onClick={onDelete}
            type="button"
          >
            <Icon className="text-[18px]" name="delete_outline" />
          </button>
        </div>
      </div>
      <p className="mt-2 text-body-sm text-on-surface-variant">{IMPORTANCE_HINT[importance]}</p>

      <div className="mt-3 grid min-w-0 grid-cols-1 gap-3.5 md:grid-cols-2">
        <label className="block min-w-0">
          <span className="mb-1 block text-label-sm font-semibold text-on-surface">Question</span>
          <input
            className={inputClass}
            disabled={disabled}
            onChange={(event) => onChange({ ...field, label: event.target.value })}
            type="text"
            value={field.label}
          />
        </label>
        <label className="block min-w-0">
          <span className="mb-1 block text-label-sm font-semibold text-on-surface">
            Summary for candidates
          </span>
          <input
            className={inputClass}
            disabled={disabled}
            maxLength={200}
            onChange={(event) =>
              onChange({ ...field, condition: { ...field.condition, summary: event.target.value } })
            }
            type="text"
            value={field.condition.summary}
          />
        </label>
      </div>

      <div className="mt-3.5 flex flex-col gap-2.5 border-t border-surface-container pt-3">
        <ConditionRule disabled={disabled} field={field} onChange={onChange} />
        {importance === "must" && field.knockout ? (
          <ReasonInput
            disabled={disabled}
            onChange={(reason) => onChange(withReason(field, reason))}
            value={field.knockout.reason}
          />
        ) : null}
        {importance === "preferred" && field.scoring ? (
          <WeightInput
            disabled={disabled}
            onChange={(weight) => onChange(withWeight(field, weight))}
            weight={field.scoring.weight}
          />
        ) : null}
      </div>

      <FieldNotices blocked={blocked} warnings={warnings} />
    </article>
  );
}

function ConditionRule({
  field,
  disabled,
  onChange,
}: {
  field: ConditionField;
  disabled: boolean;
  onChange: (field: ConditionField) => void;
}) {
  if (field.type === "number") {
    return <SalaryEditor disabled={disabled} field={field} onChange={onChange} />;
  }
  if (field.condition.importance === "info") {
    return (
      <p className="text-body-sm text-on-surface-variant">Options: {field.options.join(", ")}</p>
    );
  }
  const scale = ORDERED_SCALES[field.condition.preset];
  if (scale) {
    return (
      <label className="flex flex-wrap items-center gap-2 text-label-sm text-on-surface">
        {scale.label}:
        <select
          className="rounded border border-outline-variant bg-surface-bright px-2 py-1 text-body-sm disabled:opacity-60"
          disabled={disabled}
          onChange={(event) => onChange(withThreshold(field, event.target.value))}
          value={thresholdOf(field)}
        >
          {scale.levels.map((level) => (
            <option key={level} value={level}>
              {level}
            </option>
          ))}
        </select>
      </label>
    );
  }
  const passing = passingAnswers(field);
  return (
    <div>
      <p className="mb-1 text-label-sm font-semibold text-on-surface">Answers that meet this condition</p>
      <div className="flex flex-wrap gap-3">
        {field.options.map((option) => {
          const checked = passing.includes(option);
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
                  onChange(
                    withPassing(
                      field,
                      checked ? passing.filter((value) => value !== option) : [...passing, option],
                    ),
                  )
                }
                type="checkbox"
              />
              {option}
            </label>
          );
        })}
      </div>
    </div>
  );
}

function SalaryEditor({
  field,
  disabled,
  onChange,
}: {
  field: ConditionField;
  disabled: boolean;
  onChange: (field: ConditionField) => void;
}) {
  const salary = field.condition.salary;
  if (!salary) {
    return null;
  }
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex flex-wrap items-center gap-4">
        <label className="flex items-center gap-1.5 text-label-sm text-on-surface">
          Currency:
          <input
            className={smallInputClass}
            disabled={disabled}
            maxLength={3}
            onChange={(event) =>
              onChange(withSalary(field, { ...salary, currency: event.target.value.toUpperCase() }))
            }
            type="text"
            value={salary.currency}
          />
        </label>
        <label className="flex items-center gap-1.5 text-label-sm text-on-surface">
          Range min:
          <input
            className={cn(smallInputClass, "w-24")}
            disabled={disabled}
            min={0}
            onChange={(event) =>
              onChange(withSalary(field, { ...salary, min: numberOrNull(event.target.value) ?? 0 }))
            }
            type="number"
            value={salary.min}
          />
        </label>
        <label className="flex items-center gap-1.5 text-label-sm text-on-surface">
          Range max:
          <input
            className={cn(smallInputClass, "w-24")}
            disabled={disabled}
            min={0}
            onChange={(event) =>
              onChange(withSalary(field, { ...salary, max: numberOrNull(event.target.value) ?? 0 }))
            }
            type="number"
            value={salary.max}
          />
        </label>
      </div>
      <p className="text-body-sm text-on-surface-variant">
        Expected salaries at or below the maximum meet this condition, including those below the
        minimum.
      </p>
    </div>
  );
}
