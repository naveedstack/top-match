"use client";

import { useRouter } from "next/navigation";
import { useEffect, useSyncExternalStore } from "react";

import { AuthErrorBanner } from "@/components/auth/auth-error-banner";
import { Icon } from "@/components/icon";
import { usePublicJob } from "@/hooks/use-jobs";
import { getApiErrorMessage, isNotFoundError } from "@/lib/api-error";
import { readApplySession } from "@/lib/apply-session";

function subscribeApplySession() {
  return () => {};
}

export function ApplySuccess({ slug }: { slug: string }) {
  const router = useRouter();
  const jobQuery = usePublicJob(slug);
  const email = useSyncExternalStore(
    subscribeApplySession,
    () => readApplySession(slug)?.email ?? null,
    () => null,
  );

  useEffect(() => {
    if (!readApplySession(slug)) {
      router.replace(`/apply/${slug}`);
    }
  }, [router, slug]);

  if (!email) {
    return <p className="text-body-md text-on-surface-variant">Loading…</p>;
  }

  if (jobQuery.isPending) {
    return <p className="text-body-md text-on-surface-variant">Loading…</p>;
  }

  if (jobQuery.isError && isNotFoundError(jobQuery.error)) {
    return (
      <div className="flex flex-col gap-space-md">
        <h1 className="text-headline-xl text-on-surface">Job not found</h1>
        <p className="text-body-md text-on-surface-variant">
          This apply link is invalid or the job is no longer available.
        </p>
      </div>
    );
  }

  if (jobQuery.isError || !jobQuery.data) {
    return <AuthErrorBanner message={getApiErrorMessage(jobQuery.error)} />;
  }

  const job = jobQuery.data;

  return (
    <main className="rounded-xl border border-outline-variant bg-surface-container-lowest p-6 shadow-sm md:p-10">
      <div className="flex flex-col items-center text-center">
        <div className="mb-5 flex size-16 items-center justify-center rounded-full border border-outline-variant bg-surface-container shadow-sm">
          <div className="flex size-11 items-center justify-center rounded-full bg-surface-container-high text-on-tertiary-container">
            <Icon className="text-[26px]" name="check" />
          </div>
        </div>
        <h1 className="mb-2 text-headline-lg tracking-tight text-on-surface md:text-headline-xl">
          Application Received
        </h1>
        <p className="max-w-lg text-body-md leading-relaxed text-on-surface-variant">
          Your application for <span className="font-semibold text-on-surface">{job.title}</span>{" "}
          has been submitted.
        </p>
      </div>

      <div className="mt-8 rounded-lg border border-outline-variant bg-surface p-5">
        <p className="mb-1 text-label-sm tracking-wider text-on-surface-variant uppercase">
          Applicant
        </p>
        <p className="text-label-lg font-medium text-on-surface">{email}</p>
      </div>

      {job.privacy_notice ? (
        <div className="mt-6 flex items-start gap-3 rounded-lg border border-outline-variant bg-surface p-3.5">
          <Icon className="mt-0.5 shrink-0 text-[20px] text-secondary" name="lock" />
          <p className="text-body-sm leading-relaxed text-on-surface-variant">{job.privacy_notice}</p>
        </div>
      ) : null}
    </main>
  );
}
