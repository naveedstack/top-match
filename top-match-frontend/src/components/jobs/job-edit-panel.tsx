"use client";

import { useEffect, useState, type FormEvent } from "react";

import { AuthErrorBanner } from "@/components/auth/auth-error-banner";
import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { RichTextEditor } from "@/components/ui/rich-text-editor";
import { Textarea } from "@/components/ui/textarea";
import { useUpdateJob } from "@/hooks/use-jobs";
import {
  REQUIREMENTS_TARGET,
  getApiErrorMessage,
  getApiGuardrailErrors,
  guardrailMessage,
} from "@/lib/api-error";
import { richTextIsEmpty } from "@/lib/rich-text";
import type { JobDetail } from "@/types/jobs";

const TITLE_MAX = 200;

type JobEditPanelProps = {
  job: JobDetail;
  onClose: () => void;
};

export function JobEditPanel({ job, onClose }: JobEditPanelProps) {
  const updateJob = useUpdateJob(job.id);
  const [title, setTitle] = useState(job.title);
  const [description, setDescription] = useState(job.description);
  const [requirements, setRequirements] = useState(job.requirements);
  const [titleError, setTitleError] = useState("");
  const [descriptionError, setDescriptionError] = useState("");
  const [requirementsError, setRequirementsError] = useState("");
  const [formError, setFormError] = useState("");

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

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

    if (!valid) {
      return;
    }

    try {
      await updateJob.mutateAsync({
        title: trimmedTitle,
        description: description.trim(),
        requirements: trimmedRequirements,
      });
      onClose();
    } catch (error) {
      setRequirementsError(
        guardrailMessage(
          getApiGuardrailErrors(error).filter((item) => item.target === REQUIREMENTS_TARGET),
        ),
      );
      setFormError(getApiErrorMessage(error));
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-[rgba(15,23,42,0.4)]"
      onClick={onClose}
      role="presentation"
    >
      <aside
        aria-labelledby="edit-job-title"
        className="flex h-full w-full max-w-lg flex-col border-l border-outline-variant bg-surface-container-lowest shadow-2xl"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
      >
        <form className="flex h-full flex-col" noValidate onSubmit={onSubmit}>
          <div className="flex items-center justify-between border-b border-outline-variant p-space-lg pb-space-md">
            <div>
              <p className="text-label-sm font-semibold tracking-wider text-secondary uppercase">
                Job
              </p>
              <h2 className="text-headline-md text-on-surface" id="edit-job-title">
                Edit Job Details
              </h2>
            </div>
            <button
              aria-label="Close"
              className="rounded-lg p-1 text-on-surface-variant hover:bg-surface-container"
              onClick={onClose}
              type="button"
            >
              <Icon name="close" />
            </button>
          </div>

          <div className="flex flex-1 flex-col gap-space-md overflow-y-auto p-space-lg">
            {formError ? <AuthErrorBanner message={formError} /> : null}
            <Input
              error={titleError}
              id="edit-job-title-field"
              label="Job Title"
              maxLength={TITLE_MAX}
              onChange={(event) => setTitle(event.target.value)}
              required
              type="text"
              value={title}
            />
            <RichTextEditor
              error={descriptionError}
              id="edit-job-description"
              label="Job Overview & Responsibilities"
              onChange={setDescription}
              required
              value={description}
            />
            <Textarea
              error={requirementsError}
              id="edit-job-requirements"
              label="Requirements & AI Evaluation Rubric"
              onChange={(event) => setRequirements(event.target.value)}
              required
              rows={7}
              value={requirements}
            />
          </div>

          <div className="flex justify-end gap-space-sm border-t border-outline-variant bg-surface p-space-md">
            <Button onClick={onClose} type="button" variant="outline">
              Cancel
            </Button>
            <Button pending={updateJob.isPending} type="submit">
              Save Changes
            </Button>
          </div>
        </form>
      </aside>
    </div>
  );
}
