"use client";

import { useEffect, useState } from "react";

import { AuthErrorBanner } from "@/components/auth/auth-error-banner";
import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { useCloseJob } from "@/hooks/use-jobs";
import { getApiErrorMessage } from "@/lib/api-error";

type JobCloseDialogProps = {
  jobId: string;
  onClose: () => void;
};

export function JobCloseDialog({ jobId, onClose }: JobCloseDialogProps) {
  const closeJob = useCloseJob(jobId);
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

  async function onConfirm() {
    setFormError("");
    try {
      await closeJob.mutateAsync();
      onClose();
    } catch (error) {
      setFormError(getApiErrorMessage(error));
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(15,23,42,0.4)] p-space-md"
      onClick={onClose}
      role="presentation"
    >
      <div
        aria-labelledby="close-job-title"
        className="flex w-full max-w-md flex-col gap-space-md rounded-xl border border-outline-variant bg-surface-container-lowest p-space-lg shadow-2xl"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
      >
        <div className="flex items-center gap-space-sm">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-error-container/50 text-error">
            <Icon name="warning" />
          </div>
          <div>
            <h2 className="text-headline-sm font-semibold text-on-surface" id="close-job-title">
              Close this job?
            </h2>
            <p className="text-label-sm font-medium text-error">This cannot be undone</p>
          </div>
        </div>
        <p className="text-body-md text-on-surface-variant">
          Closing stops new applications. Candidate resumes and scores are deleted{" "}
          <span className="font-semibold text-on-surface">30 days</span> after close.
        </p>
        {formError ? <AuthErrorBanner message={formError} /> : null}
        <div className="mt-space-sm flex items-center justify-end gap-space-sm">
          <Button onClick={onClose} type="button" variant="outline">
            Nevermind
          </Button>
          <button
            className="inline-flex items-center justify-center rounded-lg bg-error px-space-md py-1.5 text-label-md text-on-error hover:bg-on-error-container disabled:pointer-events-none disabled:opacity-50"
            disabled={closeJob.isPending}
            onClick={() => void onConfirm()}
            type="button"
          >
            {closeJob.isPending ? "Closing…" : "Confirm & Close Job"}
          </button>
        </div>
      </div>
    </div>
  );
}
