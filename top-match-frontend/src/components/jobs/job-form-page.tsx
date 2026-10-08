"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { AuthErrorBanner } from "@/components/auth/auth-error-banner";
import { FormBuilderWorkspace } from "@/components/forms/form-builder-workspace";
import { FormCandidatePreview } from "@/components/forms/form-candidate-preview";
import { FormWorkspaceFrame } from "@/components/forms/form-workspace-frame";
import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/auth-context";
import { useJob, useUpdateJob } from "@/hooks/use-jobs";
import { getApiErrorMessage, getApiGuardrailErrors, isNotFoundError } from "@/lib/api-error";
import { validateFormFields } from "@/lib/form-validation";
import type { FormField, GuardrailError } from "@/types/forms";
import { totalApplications } from "@/types/jobs";

function displayUrl(url: string): string {
  return url.replace(/^https?:\/\//, "");
}

export function JobFormPage({ jobId }: { jobId: string }) {
  const router = useRouter();
  const { user } = useAuth();
  const jobQuery = useJob(jobId);
  const job = jobQuery.data;
  const updateJob = useUpdateJob(jobId);
  const [fields, setFields] = useState<FormField[] | null>(null);
  const [fieldsError, setFieldsError] = useState("");
  const [formError, setFormError] = useState("");
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState(false);
  const [savedWithWarnings, setSavedWithWarnings] = useState(false);
  const [blockedFields, setBlockedFields] = useState<GuardrailError[]>([]);

  const draft = fields ?? job?.form_fields ?? [];
  const locked = job?.form_locked ?? false;
  const applicationCount = job ? totalApplications(job.application_counts) : 0;

  async function copyLink() {
    if (!job) {
      return;
    }
    setCopyError(false);
    try {
      await navigator.clipboard.writeText(job.public_url);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopyError(true);
    }
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (locked) {
      router.push(`/jobs/${jobId}`);
      return;
    }
    const message = validateFormFields(draft);
    if (message) {
      setFieldsError(message);
      return;
    }
    setFieldsError("");
    setFormError("");
    try {
      const saved = await updateJob.mutateAsync({ form_fields: draft });
      if (saved.form_warnings.length > 0) {
        // Saved, but stay so the recruiter sees the warnings on the fields.
        setSavedWithWarnings(true);
        return;
      }
      router.push(`/jobs/${jobId}`);
    } catch (error) {
      setBlockedFields(getApiGuardrailErrors(error));
      setFormError(getApiErrorMessage(error));
    }
  }

  if (jobQuery.isPending) {
    return <p className="p-space-lg text-body-md text-on-surface-variant">Loading…</p>;
  }

  if (jobQuery.isError || !job) {
    if (jobQuery.error && isNotFoundError(jobQuery.error)) {
      return (
        <div className="flex flex-col gap-space-md p-space-lg">
          <Link
            className="inline-flex items-center gap-1.5 text-label-md text-on-surface-variant hover:text-secondary"
            href="/jobs"
          >
            <Icon className="text-[16px]" name="arrow_back" />
            Back to Jobs
          </Link>
          <h1 className="text-headline-xl text-on-surface">Job not found</h1>
          <p className="text-body-md text-on-surface-variant">
            This job does not exist or is not in your company workspace.
          </p>
        </div>
      );
    }
    return (
      <div className="p-space-lg">
        <AuthErrorBanner message={getApiErrorMessage(jobQuery.error)} />
      </div>
    );
  }

  return (
    <form className="flex h-full min-h-0 flex-col overflow-hidden" noValidate onSubmit={onSubmit}>
      <FormWorkspaceFrame
        builder={
          <div className="flex min-w-0 flex-col gap-6 px-6 py-8">
            {locked ? (
              <p className="rounded-lg border border-outline-variant bg-surface-container-low p-space-sm text-body-sm text-on-surface-variant">
                Candidates have already applied. The questions can no longer be changed.
              </p>
            ) : null}
            {formError ? <AuthErrorBanner message={formError} /> : null}
            {savedWithWarnings ? (
              <p className="rounded-lg border border-outline-variant bg-surface-container-low p-space-sm text-body-sm text-on-surface-variant">
                Form saved with warnings. Review them on the questions below before sharing the
                apply link.
              </p>
            ) : null}
            <FormBuilderWorkspace
              blocked={blockedFields}
              disabled={locked}
              error={fieldsError}
              fields={draft}
              onChange={(next) => {
                setFieldsError("");
                setSavedWithWarnings(false);
                setBlockedFields([]);
                setFields(next);
              }}
              warnings={job.form_warnings}
            />
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-outline-variant pt-4">
              <p className="flex items-center gap-1.5 text-body-sm text-on-surface-variant">
                <Icon className="text-[16px] text-secondary" name="info" />
                {locked
                  ? "This form is locked."
                  : "You can edit this until the first application arrives."}
              </p>
              <div className="flex items-center gap-2">
                <Button onClick={() => router.push(`/jobs/${jobId}`)} type="button" variant="outline">
                  {locked ? "Close" : "Cancel"}
                </Button>
                {locked ? null : (
                  <Button pending={updateJob.isPending} type="submit">
                    <Icon className="text-[18px]" name="check" />
                    Save form
                  </Button>
                )}
              </div>
            </div>
          </div>
        }
        preview={
          <div className="min-w-0 px-6 py-8">
            <FormCandidatePreview
              companyName={user?.company_name}
              description={job.description}
              fields={draft}
              requirements={job.requirements}
              screeningDisclaimer={job.screening_disclaimer}
              title={job.title}
            />
          </div>
        }
        subheader={
          <>
            <section className="border-b border-outline-variant bg-surface-container-lowest px-space-lg py-2.5">
              <div className="mx-auto flex max-w-[1440px] flex-wrap items-center justify-between gap-space-md">
                <div className="flex flex-wrap items-center gap-space-sm">
                  <nav className="flex items-center gap-1.5 text-label-md text-on-surface-variant">
                    <Link className="hover:text-secondary" href="/jobs">
                      Jobs
                    </Link>
                    <span className="text-outline">/</span>
                    <Link className="max-w-[16rem] truncate hover:text-secondary" href={`/jobs/${jobId}`}>
                      {job.title}
                    </Link>
                    <span className="text-outline">/</span>
                    <span className="font-semibold text-on-surface">Application Form</span>
                  </nav>
                  <div className="mx-1 hidden h-3.5 w-px bg-outline-variant sm:block" />
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-outline-variant bg-surface-container-low px-2 py-0.5 text-label-sm text-on-surface-variant">
                    <span className="size-1.5 rounded-full bg-amber-500" />
                    {applicationCount} {applicationCount === 1 ? "Application" : "Applications"}
                  </span>
                  {locked ? (
                    <span className="inline-flex items-center gap-1 rounded-full border border-outline-variant bg-surface-container-low px-2.5 py-0.5 text-label-sm text-on-surface-variant">
                      <Icon className="text-[14px]" name="lock" />
                      Form locked
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 rounded-full border border-secondary-fixed bg-surface-container px-2.5 py-0.5 text-label-sm text-on-secondary-container">
                      <Icon className="text-[14px]" name="lock_open" />
                      Form editable
                    </span>
                  )}
                </div>
                <div className="flex min-w-0 max-w-full items-center gap-1.5 rounded-md border border-outline-variant bg-surface-container-low px-2.5 py-1">
                  <span className="shrink-0 text-label-sm text-on-surface-variant">Public URL:</span>
                  <span className="min-w-0 truncate select-all font-mono text-label-sm text-on-surface">
                    {displayUrl(job.public_url)}
                  </span>
                  <button
                    className="rounded p-0.5 text-secondary hover:bg-surface-container"
                    onClick={() => void copyLink()}
                    title="Copy public link"
                    type="button"
                  >
                    <Icon className="text-[15px]" name={copied ? "check" : "content_copy"} />
                  </button>
                </div>
              </div>
            </section>
            {copyError ? (
              <div className="border-b border-outline-variant px-space-lg py-3">
                <AuthErrorBanner message="Could not copy the apply link." />
              </div>
            ) : null}
          </>
        }
      />
    </form>
  );
}
