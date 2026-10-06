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
import { Input } from "@/components/ui/input";
import { RichTextEditor } from "@/components/ui/rich-text-editor";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/context/auth-context";
import { useCreateJob } from "@/hooks/use-jobs";
import { getApiErrorMessage } from "@/lib/api-error";
import { validateFormFields } from "@/lib/form-validation";
import { richTextIsEmpty } from "@/lib/rich-text";
import type { FormField } from "@/types/forms";

const TITLE_MAX = 200;

export function CreateJobForm() {
  const router = useRouter();
  const { user } = useAuth();
  const createJob = useCreateJob();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [requirements, setRequirements] = useState("");
  const [formFields, setFormFields] = useState<FormField[]>([]);
  const [titleError, setTitleError] = useState("");
  const [descriptionError, setDescriptionError] = useState("");
  const [requirementsError, setRequirementsError] = useState("");
  const [formFieldsError, setFormFieldsError] = useState("");
  const [formError, setFormError] = useState("");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedTitle = title.trim();
    const trimmedRequirements = requirements.trim();
    let valid = true;
    setFormError("");

    if (!trimmedTitle) {
      setTitleError("Job title is required");
      valid = false;
    } else if (trimmedTitle.length > TITLE_MAX) {
      setTitleError(`Job title must be at most ${TITLE_MAX} characters`);
      valid = false;
    } else {
      setTitleError("");
    }

    if (richTextIsEmpty(description)) {
      setDescriptionError("Description is required");
      valid = false;
    } else {
      setDescriptionError("");
    }

    if (!trimmedRequirements) {
      setRequirementsError("Requirements are required");
      valid = false;
    } else {
      setRequirementsError("");
    }

    const fieldsMessage = validateFormFields(formFields);
    if (fieldsMessage) {
      setFormFieldsError(fieldsMessage);
      valid = false;
    } else {
      setFormFieldsError("");
    }

    if (!valid) {
      return;
    }

    try {
      const job = await createJob.mutateAsync({
        title: trimmedTitle,
        description: description.trim(),
        requirements: trimmedRequirements,
        form_fields: formFields,
      });
      router.replace(`/jobs/${job.id}`);
    } catch (error) {
      setFormError(getApiErrorMessage(error));
    }
  }

  return (
    <form className="flex h-full min-h-0 flex-col overflow-hidden" noValidate onSubmit={onSubmit}>
      <FormWorkspaceFrame
        builder={
          <div className="flex min-w-0 flex-col gap-6 px-6 py-8">
            <div>
              <h1 className="text-headline-lg font-bold tracking-tight text-on-surface">Create a job</h1>
              <p className="mt-1 text-body-md text-on-surface-variant">
                Define the role, then add extra application questions. The candidate preview on the
                right updates as you type.
              </p>
            </div>
            {formError ? <AuthErrorBanner message={formError} /> : null}
            <Input
              error={titleError}
              helper="Displayed publicly on the candidate application page."
              id="job-title"
              label="Job Title"
              maxLength={TITLE_MAX}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="e.g. Senior Backend Engineer"
              required
              type="text"
              value={title}
            />
            <div>
              <p className="mb-1.5 text-label-md font-medium text-on-surface">Public apply link</p>
              <div className="flex items-center rounded-lg border border-outline-variant bg-surface-container-low px-space-md py-2.5">
                <Icon className="mr-2 text-[18px] text-secondary" name="link" />
                <p className="text-body-sm text-on-surface-variant">
                  A unique{" "}
                  <span className="font-mono text-on-surface">
                    /{user?.company_slug ?? "company"}/{"{job}"}
                  </span>{" "}
                  URL is created when you save. Copy it on the next screen.
                </p>
              </div>
            </div>
            <RichTextEditor
              error={descriptionError}
              id="job-description"
              label="Job Overview & Responsibilities"
              onChange={setDescription}
              placeholder="Describe the team, mission, daily responsibilities, and technical stack..."
              required
              value={description}
            />
            <div className="flex flex-col gap-2">
              <div className="flex items-start gap-space-sm rounded-lg border border-secondary-fixed bg-surface-container-low p-space-md">
                <Icon className="mt-0.5 shrink-0 text-[20px] text-secondary" name="info" />
                <p className="text-body-sm leading-snug text-on-surface">
                  The AI scores resumes{" "}
                  <span className="font-semibold text-secondary">only against these requirements</span>.
                  Be specific about must-haves, experience, and technical competencies.
                </p>
              </div>
              <Textarea
                className="font-mono text-sm"
                error={requirementsError}
                extra={
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-secondary-fixed px-2 py-0.5 text-label-sm font-semibold text-on-secondary-fixed">
                    <span className="size-1.5 rounded-full bg-secondary" />
                    Crucial for Scoring
                  </span>
                }
                id="job-requirements"
                label="Requirements & AI Evaluation Rubric"
                onChange={(event) => setRequirements(event.target.value)}
                placeholder={"- 5+ years building APIs in Python\n- Experience with FastAPI and PostgreSQL"}
                required
                rows={7}
                value={requirements}
              />
            </div>
            <FormBuilderWorkspace
              error={formFieldsError}
              fields={formFields}
              onChange={(next) => {
                setFormFieldsError("");
                setFormFields(next);
              }}
            />
            <fieldset className="flex flex-col gap-2 border-t border-outline-variant pt-2">
              <legend className="text-label-md font-medium text-on-surface">Data deletion schedule</legend>
              <div className="flex items-start gap-space-sm rounded-lg border border-outline-variant bg-surface-bright p-3.5">
                <input
                  checked
                  className="mt-1 size-4 border-outline-variant"
                  disabled
                  id="retention-30d"
                  name="retention"
                  type="radio"
                />
                <div>
                  <label className="text-label-lg font-medium text-on-surface" htmlFor="retention-30d">
                    Auto-delete candidate resumes and scores 30 days after job closure
                  </label>
                  <p className="mt-0.5 text-body-sm text-on-surface-variant">
                    Server default. This is not sent with the job; retention is always 30 days.
                  </p>
                </div>
              </div>
            </fieldset>
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-outline-variant pt-4">
              <p className="flex items-center gap-1.5 text-body-sm text-on-surface-variant">
                <Icon className="text-[16px] text-secondary" name="info" />
                You can add more questions later until the first application arrives.
              </p>
              <div className="flex items-center gap-2">
                <Button onClick={() => router.push("/jobs")} type="button" variant="outline">
                  Cancel
                </Button>
                <Button pending={createJob.isPending} type="submit">
                  Create Job &amp; Generate Apply Link
                  <Icon className="text-[18px]" name="arrow_forward" />
                </Button>
              </div>
            </div>
          </div>
        }
        preview={
          <div className="min-w-0 px-6 py-8">
            <FormCandidatePreview
              companyName={user?.company_name}
              description={description}
              fields={formFields}
              requirements={requirements}
              title={title}
            />
          </div>
        }
        subheader={
          <section className="border-b border-outline-variant bg-surface-container-lowest px-space-lg py-2.5">
            <div className="mx-auto flex max-w-[1440px] flex-wrap items-center justify-between gap-space-md">
              <nav className="flex items-center gap-1.5 text-label-md text-on-surface-variant">
                <Link className="hover:text-secondary" href="/jobs">
                  Jobs
                </Link>
                <span className="text-outline">/</span>
                <span className="font-semibold text-on-surface">Create a Job</span>
              </nav>
              <span className="inline-flex items-center gap-1 rounded-full border border-secondary-fixed bg-surface-container px-2.5 py-0.5 text-label-sm text-on-secondary-container">
                <Icon className="text-[14px]" name="visibility" />
                Live candidate preview
              </span>
            </div>
          </section>
        }
      />
    </form>
  );
}
