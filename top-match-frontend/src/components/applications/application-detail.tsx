"use client";

import Link from "next/link";
import { useCallback, useState, type ReactNode } from "react";

import { ResumePreview } from "@/components/applications/resume-preview";
import { AuthErrorBanner } from "@/components/auth/auth-error-banner";
import { Icon } from "@/components/icon";
import { Badge } from "@/components/ui/badge";
import { Banner } from "@/components/ui/banner";
import { Button } from "@/components/ui/button";
import { useApplication, useRescoreApplication } from "@/hooks/use-applications";
import { useExportJob, useJob } from "@/hooks/use-jobs";
import { getApiErrorMessage, isNotFoundError } from "@/lib/api-error";
import { csvFilenameFromTitle, downloadTextFile } from "@/lib/download";
import type { Citation } from "@/types/applications";

type ApplicationDetailViewProps = {
  jobId: string;
  applicationId: string;
};

function formatAppliedAt(iso: string): string {
  return new Intl.DateTimeFormat(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(iso));
}

function NotFoundState({
  href,
  title,
  message,
  backLabel,
}: {
  href: string;
  title: string;
  message: string;
  backLabel: string;
}) {
  return (
    <div className="flex flex-col gap-space-md">
      <Link
        className="inline-flex items-center gap-1.5 text-label-md text-on-surface-variant hover:text-secondary"
        href={href}
      >
        <Icon className="text-[16px]" name="arrow_back" />
        {backLabel}
      </Link>
      <h1 className="text-headline-xl text-on-surface">{title}</h1>
      <p className="text-body-md text-on-surface-variant">{message}</p>
    </div>
  );
}

function ScoreMark({ score }: { score: number | null }) {
  if (score === null) {
    return (
      <div className="flex size-16 items-center justify-center rounded-xl border border-outline-variant bg-surface-container-low">
        <span className="font-mono text-headline-sm text-on-surface-variant">—</span>
      </div>
    );
  }

  return (
    <div className="relative flex size-16 items-center justify-center rounded-xl border border-outline-variant bg-surface-container-low">
      <svg className="size-14 -rotate-90" viewBox="0 0 36 36">
        <path
          className="text-surface-variant"
          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
        />
        <path
          className="text-secondary"
          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          fill="none"
          stroke="currentColor"
          strokeDasharray={`${score}, 100`}
          strokeLinecap="round"
          strokeWidth="3"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="font-mono text-headline-sm leading-none font-bold text-on-surface">
          {score}
        </span>
        <span className="text-[9px] text-outline">/ 100</span>
      </div>
    </div>
  );
}

export function ApplicationDetailView({ jobId, applicationId }: ApplicationDetailViewProps) {
  const jobQuery = useJob(jobId);
  const applicationQuery = useApplication(applicationId);
  const exportJob = useExportJob(jobId);
  const rescore = useRescoreApplication(jobId, applicationId);
  const [actionError, setActionError] = useState("");

  const job = jobQuery.data;
  const application = applicationQuery.data;

  const refetchApplication = applicationQuery.refetch;
  const onRefreshUrl = useCallback(async () => {
    const result = await refetchApplication();
    return result.data?.resume_url ?? null;
  }, [refetchApplication]);

  async function onExport() {
    setActionError("");
    try {
      const csv = await exportJob.mutateAsync({ application_ids: [applicationId] });
      downloadTextFile(csv, csvFilenameFromTitle(job?.title ?? "job"));
    } catch (error) {
      setActionError(getApiErrorMessage(error));
    }
  }

  async function onRescore() {
    setActionError("");
    try {
      await rescore.mutateAsync();
    } catch (error) {
      setActionError(getApiErrorMessage(error));
    }
  }

  if (jobQuery.isError && isNotFoundError(jobQuery.error)) {
    return (
      <NotFoundState
        backLabel="Back to Jobs"
        href="/jobs"
        message="This job does not exist or is not in your company workspace."
        title="Job not found"
      />
    );
  }

  if (applicationQuery.isError && isNotFoundError(applicationQuery.error)) {
    return (
      <NotFoundState
        backLabel="Back to Leaderboard"
        href={`/jobs/${jobId}`}
        message="This application does not exist or is not in your company workspace."
        title="Application not found"
      />
    );
  }

  if (jobQuery.isError) {
    return <AuthErrorBanner message={getApiErrorMessage(jobQuery.error)} />;
  }

  if (applicationQuery.isError) {
    return <AuthErrorBanner message={getApiErrorMessage(applicationQuery.error)} />;
  }

  if (jobQuery.isPending || applicationQuery.isPending || !job || !application) {
    return <p className="text-body-md text-on-surface-variant">Loading…</p>;
  }

  const inFlight = application.status === "received" || application.status === "processing";

  return (
    <div className="flex flex-col gap-space-lg">
      {job.screening_disclaimer ? <Banner>{job.screening_disclaimer}</Banner> : null}

      <nav className="flex flex-wrap items-center gap-2 text-label-md text-on-surface-variant">
        <Link className="hover:text-secondary" href="/jobs">
          Jobs
        </Link>
        <span className="text-outline">/</span>
        <Link className="max-w-[280px] truncate hover:text-secondary md:max-w-none" href={`/jobs/${jobId}`}>
          {job.title}
        </Link>
        <span className="text-outline">/</span>
        <span className="font-semibold text-on-surface">{application.email}</span>
      </nav>

      {actionError ? <AuthErrorBanner message={actionError} /> : null}

      <section className="rounded-xl border border-outline-variant bg-surface-container-lowest p-space-md shadow-sm md:p-space-lg">
        <div className="flex flex-col justify-between gap-space-lg lg:flex-row lg:items-center">
          <div className="flex flex-col items-start gap-space-md sm:flex-row sm:items-center">
            <div className="flex items-center gap-3 pr-2 sm:border-r sm:border-outline-variant">
              <ScoreMark score={application.score} />
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={application.status} />
                  <span className="text-body-sm text-outline">
                    Applied {formatAppliedAt(application.created_at)}
                  </span>
                </div>
                <h1 className="mt-0.5 text-headline-lg font-bold tracking-tight text-on-surface">
                  {application.email}
                </h1>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {application.needs_review ? (
                <span className="inline-flex items-center gap-1.5 rounded border border-amber-300 bg-amber-50 px-2.5 py-1 text-label-md text-amber-800">
                  <Icon className="text-[16px] text-amber-700" name="warning" />
                  Needs review
                </span>
              ) : null}
              {application.injection_suspected ? (
                <span className="inline-flex items-center gap-1.5 rounded border border-rose-200 bg-rose-50 px-2.5 py-1 text-label-md text-rose-800">
                  <Icon className="text-[16px] text-error" name="security" />
                  Possible prompt injection
                </span>
              ) : null}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-space-sm">
            <Link
              className="inline-flex items-center gap-1.5 rounded-lg border border-outline-variant bg-surface-container-lowest px-3 py-2 text-label-lg text-on-surface hover:bg-surface-container-low"
              href={`/jobs/${jobId}`}
            >
              <Icon className="text-[18px]" name="arrow_back" />
              Back to Leaderboard
            </Link>
            {application.resume_url ? (
              <a
                className="inline-flex items-center gap-1.5 rounded-lg border border-outline-variant bg-surface-container-lowest px-3 py-2 text-label-lg text-secondary hover:bg-surface-container-low"
                href="#pdf-preview"
              >
                <Icon className="text-[18px]" name="open_in_new" />
                Open PDF
              </a>
            ) : null}
            <Button onClick={() => void onExport()} pending={exportJob.isPending} type="button">
              <Icon name="download" />
              Export CSV
            </Button>
            {application.status === "failed" ? (
              <Button
                onClick={() => void onRescore()}
                pending={rescore.isPending}
                type="button"
                variant="destructive"
              >
                <Icon name="refresh" />
                Rescore
              </Button>
            ) : null}
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-space-lg lg:grid-cols-12">
        <section className="flex flex-col gap-space-lg lg:col-span-7">
          {inFlight ? (
            <p className="rounded-xl border border-outline-variant bg-surface-container-lowest p-space-lg text-body-md text-on-surface-variant shadow-sm">
              Scoring in progress. This page updates automatically.
            </p>
          ) : null}

          {application.status === "refused" && application.refusal_reason ? (
            <article className="rounded-xl border border-outline-variant bg-surface-container-lowest p-space-lg shadow-sm">
              <div className="mb-space-md flex items-center gap-2 border-b border-outline-variant pb-space-md">
                <Icon className="text-on-surface-variant" name="block" />
                <h2 className="text-headline-sm font-semibold text-on-surface">Refusal reason</h2>
              </div>
              <p className="text-body-md text-on-surface-variant">{application.refusal_reason}</p>
            </article>
          ) : null}

          {application.status === "failed" ? (
            <p className="rounded-xl border border-outline-variant bg-surface-container-lowest p-space-lg text-body-md text-on-surface-variant shadow-sm">
              Scoring failed. Rescore to try again.
            </p>
          ) : null}

          {application.key_strengths.length > 0 ? (
            <EvidenceCard
              count={application.key_strengths.length}
              icon="fact_check"
              title="Key Strengths"
            >
              {application.key_strengths.map((item, index) => (
                <div
                  className="rounded-lg border border-outline-variant bg-surface p-space-md"
                  key={`strength-${index}`}
                >
                  <p className="text-headline-sm text-on-surface">{item}</p>
                </div>
              ))}
            </EvidenceCard>
          ) : null}

          {application.missing_requirements.length > 0 ? (
            <EvidenceCard
              count={application.missing_requirements.length}
              icon="warning"
              title="Missing Requirements"
              tone="attention"
            >
              {application.missing_requirements.map((item, index) => (
                <div
                  className="rounded-lg border border-outline-variant bg-surface p-space-md"
                  key={`missing-${index}`}
                >
                  <p className="text-headline-sm text-on-surface">{item}</p>
                </div>
              ))}
            </EvidenceCard>
          ) : null}

          {application.citations.length > 0 ? (
            <EvidenceCard count={application.citations.length} icon="format_quote" title="Citations">
              {application.citations.map((citation, index) => (
                <CitationBlock citation={citation} key={`citation-${index}`} />
              ))}
            </EvidenceCard>
          ) : null}
        </section>

        <section className="lg:col-span-5">
          {application.resume_url ? (
            <ResumePreview
              key={application.id}
              onRefreshUrl={onRefreshUrl}
              resumeUrl={application.resume_url}
            />
          ) : (
            <div
              className="flex min-h-[320px] items-center justify-center rounded-xl border border-outline-variant bg-surface-container-lowest p-space-lg text-body-md text-on-surface-variant shadow-sm"
              id="pdf-preview"
            >
              Resume is not available.
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function EvidenceCard({
  title,
  icon,
  count,
  tone = "default",
  children,
}: {
  title: string;
  icon: string;
  count: number;
  tone?: "default" | "attention";
  children: ReactNode;
}) {
  return (
    <article className="rounded-xl border border-outline-variant bg-surface-container-lowest p-space-lg shadow-sm">
      <div className="mb-space-md flex items-center justify-between border-b border-outline-variant pb-space-md">
        <div className="flex items-center gap-2">
          <Icon className={tone === "attention" ? "text-error" : "text-secondary"} name={icon} />
          <h2 className="text-headline-sm font-semibold text-on-surface">{title}</h2>
        </div>
        <span
          className={
            tone === "attention"
              ? "rounded bg-error-container px-2 py-0.5 text-label-sm font-semibold text-on-error-container"
              : "rounded bg-surface-container px-2 py-0.5 text-label-sm font-semibold text-secondary"
          }
        >
          {count}
        </span>
      </div>
      <div className="flex flex-col gap-space-md">{children}</div>
    </article>
  );
}

function CitationBlock({ citation }: { citation: Citation }) {
  return (
    <div className="rounded-lg border border-outline-variant bg-surface p-space-md">
      <p className="mb-2 text-label-md font-semibold tracking-wider text-secondary uppercase">
        Claim
      </p>
      <p className="mb-2 text-headline-sm font-medium text-on-surface">{citation.claim}</p>
      <blockquote className="rounded-r border-l-2 border-secondary bg-surface-container-low/50 py-2 pl-3.5 text-body-md text-on-surface-variant italic">
        {citation.quote}
      </blockquote>
    </div>
  );
}
