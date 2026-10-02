"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { AuthErrorBanner } from "@/components/auth/auth-error-banner";
import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useCreateJob } from "@/hooks/use-jobs";
import { getApiErrorMessage } from "@/lib/api-error";

const TITLE_MAX = 200;

export function CreateJobForm() {
  const router = useRouter();
  const createJob = useCreateJob();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [requirements, setRequirements] = useState("");
  const [titleError, setTitleError] = useState("");
  const [descriptionError, setDescriptionError] = useState("");
  const [requirementsError, setRequirementsError] = useState("");
  const [formError, setFormError] = useState("");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedTitle = title.trim();
    const trimmedDescription = description.trim();
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

    if (!trimmedDescription) {
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

    if (!valid) {
      return;
    }

    try {
      const job = await createJob.mutateAsync({
        title: trimmedTitle,
        description: trimmedDescription,
        requirements: trimmedRequirements,
      });
      router.replace(`/jobs/${job.id}`);
    } catch (error) {
      setFormError(getApiErrorMessage(error));
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-[1200px] flex-col gap-space-md">
      <Link
        className="inline-flex items-center gap-1.5 text-label-md text-on-surface-variant hover:text-secondary"
        href="/jobs"
      >
        <Icon className="text-[16px]" name="arrow_back" />
        Back to Jobs
      </Link>

      <div className="grid grid-cols-1 items-start gap-gutter lg:grid-cols-12">
        <div className="flex flex-col gap-space-md lg:col-span-8">
          <div>
            <h1 className="text-headline-xl tracking-tight text-on-surface">Create a Job</h1>
            <p className="mt-1.5 text-body-md leading-relaxed text-on-surface-variant">
              Define your role criteria. Once created, a unique public application URL will be
              generated for LinkedIn, Indeed, and external boards.
            </p>
          </div>

          {formError ? <AuthErrorBanner message={formError} /> : null}

          <form
            className="flex flex-col gap-space-lg rounded-xl border border-outline-variant bg-surface-container-lowest p-space-lg shadow-sm"
            noValidate
            onSubmit={onSubmit}
          >
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
                  A unique <span className="font-mono text-on-surface">/apply/{"{slug}"}</span> URL
                  is created when you save. Copy it on the next screen.
                </p>
              </div>
            </div>

            <Textarea
              error={descriptionError}
              id="job-description"
              label="Job Overview & Responsibilities"
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Describe the team, mission, daily responsibilities, and technical stack..."
              required
              rows={6}
              value={description}
            />

            <div className="flex flex-col gap-2">
              <div className="flex items-start gap-space-sm rounded-lg border border-secondary-fixed bg-surface-container-low p-space-md">
                <Icon className="mt-0.5 shrink-0 text-[20px] text-secondary" name="info" />
                <p className="text-body-sm leading-snug text-on-surface">
                  The AI scores resumes{" "}
                  <span className="font-semibold text-secondary">only against these requirements</span>
                  . Be specific about must-haves, experience, and technical competencies.
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

            <fieldset className="flex flex-col gap-2 border-t border-outline-variant pt-2">
              <legend className="text-label-md font-medium text-on-surface">
                Data deletion schedule
              </legend>
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

            <div className="flex flex-col-reverse items-center justify-between gap-space-md border-t border-outline-variant pt-space-md sm:flex-row">
              <Link
                className="w-full rounded-lg border border-outline-variant bg-surface-container-lowest px-space-md py-2.5 text-center text-label-lg text-on-surface hover:bg-surface-container-low sm:w-auto"
                href="/jobs"
              >
                Cancel
              </Link>
              <Button className="w-full sm:w-auto" pending={createJob.isPending} type="submit">
                Create Job &amp; Generate Apply Link
                <Icon className="text-[18px]" name="arrow_forward" />
              </Button>
            </div>
          </form>
        </div>

        <aside className="flex flex-col gap-space-md lg:col-span-4 lg:mt-14">
          <div className="rounded-xl border border-outline-variant bg-surface-container-lowest p-space-lg shadow-sm">
            <h2 className="mb-space-sm text-headline-sm text-on-surface">How scoring works</h2>
            <ul className="flex flex-col gap-space-sm text-body-sm leading-relaxed text-on-surface-variant">
              <li>The model scores each resume only against the requirements you enter here.</li>
              <li>Candidates apply with email and a PDF. They do not create an account.</li>
              <li>After you create the job, copy the public apply link and share it on job boards.</li>
            </ul>
          </div>
        </aside>
      </div>
    </div>
  );
}
