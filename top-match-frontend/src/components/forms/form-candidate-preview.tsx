"use client";

import { FormFieldInput } from "@/components/forms/form-field-input";
import { Icon } from "@/components/icon";
import type { FormField } from "@/types/forms";

type FormCandidatePreviewProps = {
  title: string;
  companyName?: string;
  description: string;
  requirements: string;
  screeningDisclaimer?: string;
  fields: FormField[];
};

const DEFAULT_DISCLAIMER =
  "This tool is a filtering aid. Hiring decisions must comply with local employment laws regarding AI screening.";

function requirementLines(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.replace(/^[-*•]\s*/, "").trim())
    .filter(Boolean);
}

export function FormCandidatePreview({
  title,
  companyName,
  description,
  requirements,
  screeningDisclaimer = DEFAULT_DISCLAIMER,
  fields,
}: FormCandidatePreviewProps) {
  const lines = requirementLines(requirements);
  const heading = title.trim() || "Job title";

  return (
    <div className="flex min-h-full min-w-0 max-w-full flex-col overflow-hidden rounded-xl border border-outline-variant bg-surface-container-lowest shadow-md">
      <div className="flex shrink-0 items-center justify-between border-b border-outline-variant bg-surface-container-low px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="size-2 rounded-full bg-emerald-500" />
          <span className="text-headline-sm font-semibold text-on-surface">Candidate preview</span>
          <span className="rounded bg-surface-container px-2 py-0.5 text-label-sm font-medium text-secondary">
            Live preview
          </span>
        </div>
      </div>

      <div className="flex min-w-0 flex-col gap-4 p-5">
        <div className="flex items-center justify-between border-b border-surface-container pb-3">
          <div className="flex items-center gap-1.5">
            <div className="flex size-5 items-center justify-center rounded bg-on-background text-surface-container-lowest">
              <Icon className="text-[13px]" name="filter_alt" />
            </div>
            <span className="text-headline-sm font-bold tracking-tight text-on-surface">Top Match</span>
          </div>
          <div className="flex items-center gap-1 text-label-sm text-on-surface-variant">
            <Icon className="text-[14px]" name="lock" />
            <span>Secure Application Portal</span>
          </div>
        </div>

        <div>
          <h3 className="break-words text-headline-md font-bold text-on-surface">{heading}</h3>
          {companyName ? (
            <p className="mt-0.5 text-label-md text-on-surface-variant">{companyName}</p>
          ) : null}
        </div>

          {description.trim() ? (
          <p className="whitespace-pre-wrap break-words text-body-sm leading-relaxed text-on-surface-variant">
            {description}
          </p>
        ) : (
          <p className="text-body-sm text-outline">Role overview appears here as you write it.</p>
        )}

        {lines.length > 0 ? (
          <div className="space-y-2 rounded-lg border border-outline-variant bg-surface-bright p-3">
            <span className="block text-label-sm font-bold tracking-wider text-on-surface-variant uppercase">
              Key Technical Requirements
            </span>
            <ul className="space-y-1.5 text-body-sm text-on-surface">
              {lines.map((line) => (
                <li className="flex items-start gap-2" key={line}>
                  <Icon className="mt-0.5 shrink-0 text-[16px] text-secondary" name="check_circle" />
                  <span>{line}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="space-y-1 rounded-lg border border-secondary-fixed bg-surface-container-low p-2.5">
          <div className="flex items-center gap-1.5 text-label-sm font-semibold text-secondary">
            <Icon className="text-[15px]" name="verified_user" />
            Transparency & Algorithmic Notice
          </div>
          <p className="text-xs leading-relaxed text-on-surface-variant">
            {screeningDisclaimer} Custom answers are stored for recruiter review. Only the resume PDF
            is scored.
          </p>
        </div>

        <div className="space-y-3 pt-1">
          <label className="block">
            <span className="mb-1 block text-label-sm font-semibold text-on-surface">
              Email address <span className="text-error">*</span>
            </span>
            <input
              className="w-full cursor-not-allowed rounded-lg border border-outline-variant bg-surface-container-lowest px-3 py-1.5 text-body-sm text-on-surface placeholder:text-outline"
              disabled
              placeholder="e.g. alex.chen@example.com"
              type="email"
            />
          </label>

          <div>
            <p className="mb-1 text-label-sm font-semibold text-on-surface">
              Resume PDF <span className="text-error">*</span>
            </p>
            <div className="rounded-lg border-2 border-dashed border-outline-variant bg-surface-bright p-3 text-center">
              <Icon className="mx-auto mb-1 block text-[22px] text-secondary" name="cloud_upload" />
              <span className="block text-label-sm font-medium text-on-surface">
                Drag & drop resume (PDF only, max 5 MB) *
              </span>
              <span className="mt-0.5 block text-[11px] text-on-surface-variant">
                Scored by AI rubric
              </span>
            </div>
          </div>

          {fields.map((field) => (
            <div className="min-w-0" key={field.id}>
              <FormFieldInput disabled field={field} onChange={() => {}} value={null} />
            </div>
          ))}

          <label className="flex cursor-not-allowed items-start gap-2 pt-1">
            <input
              checked
              className="mt-0.5 size-4 rounded border-outline-variant"
              disabled
              readOnly
              type="checkbox"
            />
            <span className="text-xs leading-tight text-on-surface">
              I have read the privacy and automated AI screening notices above, and consent to the
              automated evaluation of my resume against this job.{" "}
              <span className="text-error">*</span>
            </span>
          </label>

          <button
            className="flex w-full cursor-not-allowed items-center justify-center gap-2 rounded-lg bg-primary-container/60 py-2.5 text-label-lg text-on-primary opacity-75"
            disabled
            type="button"
          >
            Submit Application
            <Icon className="text-[16px]" name="arrow_forward" />
          </button>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-2 border-t border-outline-variant bg-surface-container-low p-3">
        <Icon className="shrink-0 text-[16px] text-secondary" name="info" />
        <span className="text-[11px] leading-tight text-on-surface-variant">
          This is exactly what candidates see. Custom answers are for you; only the resume PDF is
          scored by the AI.
        </span>
      </div>
    </div>
  );
}
