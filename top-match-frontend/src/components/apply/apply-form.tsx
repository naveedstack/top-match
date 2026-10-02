"use client";

import { useRouter } from "next/navigation";
import { useId, useRef, useState, type ChangeEvent, type DragEvent, type FormEvent } from "react";

import { AuthErrorBanner } from "@/components/auth/auth-error-banner";
import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useApply, useUploadResume } from "@/hooks/use-applications";
import { usePublicJob } from "@/hooks/use-jobs";
import { getApiErrorMessage, isNotFoundError } from "@/lib/api-error";
import { saveApplySession } from "@/lib/apply-session";
import { cn } from "@/lib/cn";
import { isValidEmail } from "@/lib/email";

const MAX_UPLOAD_BYTES = 5 * 1024 * 1024;

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function isPdfFile(file: File): boolean {
  return file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
}

export function ApplyForm({ slug }: { slug: string }) {
  const router = useRouter();
  const jobQuery = usePublicJob(slug);
  const uploadResume = useUploadResume();
  const apply = useApply(slug);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const consentId = useId();

  const [email, setEmail] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [consented, setConsented] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [fileError, setFileError] = useState("");
  const [consentError, setConsentError] = useState("");
  const [formError, setFormError] = useState("");
  const [pending, setPending] = useState(false);

  const job = jobQuery.data;

  function acceptFile(next: File | undefined) {
    setFormError("");
    if (!next) {
      return;
    }
    if (!isPdfFile(next)) {
      setFile(null);
      setFileError("Resume must be a PDF");
      return;
    }
    if (next.size > MAX_UPLOAD_BYTES) {
      setFile(null);
      setFileError("Resume must be at most 5 MB");
      return;
    }
    setFileError("");
    setFile(next);
  }

  function onFileInput(event: ChangeEvent<HTMLInputElement>) {
    acceptFile(event.target.files?.[0]);
    event.target.value = "";
  }

  function onDrop(event: DragEvent<HTMLButtonElement>) {
    event.preventDefault();
    setDragging(false);
    acceptFile(event.dataTransfer.files[0]);
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedEmail = email.trim();
    let valid = true;
    setFormError("");

    if (!trimmedEmail) {
      setEmailError("Email is required");
      valid = false;
    } else if (!isValidEmail(trimmedEmail)) {
      setEmailError("Enter a valid email");
      valid = false;
    } else {
      setEmailError("");
    }

    if (!file) {
      setFileError("Resume is required");
      valid = false;
    } else {
      setFileError("");
    }

    if (!consented) {
      setConsentError("Consent is required to apply");
      valid = false;
    } else {
      setConsentError("");
    }

    if (!valid || !file) {
      return;
    }

    setPending(true);
    try {
      const uploaded = await uploadResume.mutateAsync(file);
      await apply.mutateAsync({
        email: trimmedEmail,
        file_id: uploaded.id,
        consented: true,
      });
      saveApplySession(slug, trimmedEmail);
      router.replace(`/apply/${slug}/done`);
    } catch (error) {
      setFormError(getApiErrorMessage(error));
      setPending(false);
    }
  }

  if (jobQuery.isPending) {
    return <p className="text-body-md text-on-surface-variant">Loading…</p>;
  }

  if (jobQuery.isError || !job) {
    if (jobQuery.error && isNotFoundError(jobQuery.error)) {
      return (
        <div className="flex flex-col gap-space-md">
          <h1 className="text-headline-xl text-on-surface">Job not found</h1>
          <p className="text-body-md text-on-surface-variant">
            This apply link is invalid or the job is no longer available.
          </p>
        </div>
      );
    }
    return <AuthErrorBanner message={getApiErrorMessage(jobQuery.error)} />;
  }

  const closed = job.status === "closed";

  return (
    <main className="overflow-hidden rounded-xl border border-outline-variant bg-surface-container-lowest shadow-sm">
      <section className="border-b border-outline-variant p-space-lg md:p-space-xl">
        <h1 className="text-headline-xl-mobile md:text-headline-xl text-on-surface">{job.title}</h1>
      </section>

      <section className="flex flex-col gap-space-lg border-b border-outline-variant bg-surface-bright p-space-lg md:p-space-xl">
        <div>
          <h2 className="mb-space-xs flex items-center gap-space-sm text-headline-sm text-on-surface">
            <Icon className="text-[20px] text-secondary" name="subject" />
            Role Overview
          </h2>
          <p className="whitespace-pre-wrap text-body-md leading-relaxed text-on-surface-variant">
            {job.description}
          </p>
        </div>
        <div>
          <h2 className="mb-space-sm flex items-center gap-space-sm text-headline-sm text-on-surface">
            <Icon className="text-[20px] text-secondary" name="rule" />
            Requirements
          </h2>
          <p className="whitespace-pre-wrap text-body-md leading-relaxed text-on-surface-variant">
            {job.requirements}
          </p>
        </div>
      </section>

      <section className="border-b border-outline-variant bg-surface-container-low p-space-lg md:p-space-xl">
        <div className="flex items-start gap-space-md rounded-lg border border-outline-variant bg-surface-container-lowest p-space-md shadow-sm">
          <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full bg-surface-container">
            <Icon className="text-[20px] text-secondary" name="verified_user" />
          </div>
          <div className="flex flex-col gap-space-md">
            <div>
              <p className="mb-1 text-label-lg font-semibold text-on-surface">Privacy</p>
              <p className="text-body-sm leading-relaxed text-on-surface-variant">
                {job.privacy_notice}
              </p>
            </div>
            <div className="border-t border-outline-variant pt-space-sm">
              <p className="mb-1 text-label-lg font-semibold text-on-surface">AI screening</p>
              <p className="text-body-sm leading-relaxed text-on-surface-variant">
                {job.ai_screening_notice}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="p-space-lg md:p-space-xl">
        {closed ? (
          <p className="text-body-md text-on-surface-variant">
            This job is no longer accepting applications.
          </p>
        ) : (
          <form className="flex flex-col gap-space-lg" noValidate onSubmit={onSubmit}>
            {formError ? <AuthErrorBanner message={formError} /> : null}

            <Input
              autoComplete="email"
              error={emailError}
              helper="We use this to identify your application. No account is created."
              id="candidate-email"
              label="Email address"
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              required
              type="email"
              value={email}
            />

            <div>
              <p className="mb-1.5 block text-label-md font-medium text-on-surface">
                Upload Resume{" "}
                <span className="text-error" aria-hidden>
                  *
                </span>
              </p>
              <input
                accept="application/pdf,.pdf"
                className="sr-only"
                onChange={onFileInput}
                ref={fileInputRef}
                type="file"
              />
              <button
                className={cn(
                  "w-full rounded-xl border-2 border-dashed bg-surface-bright p-space-lg text-center transition-colors",
                  dragging ? "border-secondary" : "border-outline-variant hover:border-secondary",
                )}
                onClick={() => fileInputRef.current?.click()}
                onDragLeave={() => setDragging(false)}
                onDragOver={(event) => {
                  event.preventDefault();
                  setDragging(true);
                }}
                onDrop={onDrop}
                type="button"
              >
                <div className="mx-auto mb-space-sm flex size-12 items-center justify-center rounded-full bg-surface-container">
                  <Icon className="text-[24px] text-secondary" name="cloud_upload" />
                </div>
                <p className="text-label-lg text-on-surface">
                  Drag and drop your resume here, or{" "}
                  <span className="text-headline-sm text-secondary underline">browse files</span>
                </p>
                <p className="mt-1 text-body-sm text-outline">PDF only • Max 5 MB • Up to 5 pages</p>
              </button>
              {file ? (
                <div className="mt-space-sm flex items-center justify-between rounded-lg border border-outline-variant bg-surface-container-low p-space-sm md:px-space-md">
                  <div className="flex min-w-0 items-center gap-space-sm">
                    <span className="flex size-8 shrink-0 items-center justify-center rounded bg-surface-container-highest text-secondary">
                      <Icon className="text-[20px]" name="picture_as_pdf" />
                    </span>
                    <div className="min-w-0">
                      <p className="truncate text-label-md text-on-surface">{file.name}</p>
                      <p className="text-body-sm text-on-surface-variant">{formatFileSize(file.size)}</p>
                    </div>
                  </div>
                  <button
                    aria-label="Remove file"
                    className="shrink-0 rounded p-1 text-outline hover:bg-surface-container hover:text-error"
                    onClick={() => setFile(null)}
                    type="button"
                  >
                    <Icon name="close" />
                  </button>
                </div>
              ) : null}
              {fileError ? <p className="mt-1 text-body-sm text-error">{fileError}</p> : null}
            </div>

            <div>
              <label className="flex cursor-pointer items-start gap-space-sm select-none" htmlFor={consentId}>
                <input
                  checked={consented}
                  className="mt-1 size-4 rounded border-outline"
                  id={consentId}
                  onChange={(event) => setConsented(event.target.checked)}
                  type="checkbox"
                />
                <span className="text-body-sm leading-normal text-on-surface">
                  I have read the privacy and automated AI screening notices above, and consent to
                  the automated evaluation of my resume against this job.
                </span>
              </label>
              {consentError ? <p className="mt-1 text-body-sm text-error">{consentError}</p> : null}
            </div>

            <div className="flex flex-col gap-space-sm">
              <Button className="w-full py-3.5" pending={pending} type="submit">
                Submit Application
                <Icon name="arrow_forward" />
              </Button>
              <p className="text-center text-body-sm text-on-surface-variant">
                No account needed.
              </p>
            </div>
          </form>
        )}
      </section>
    </main>
  );
}
