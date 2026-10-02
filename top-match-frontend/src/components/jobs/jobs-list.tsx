"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { AuthErrorBanner } from "@/components/auth/auth-error-banner";
import { Icon } from "@/components/icon";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useJobs } from "@/hooks/use-jobs";
import { getApiErrorMessage } from "@/lib/api-error";
import { cn } from "@/lib/cn";
import type { ApplicationCounts, JobListItem, JobStatus } from "@/types/jobs";

type StatusFilter = "all" | JobStatus;

const PIPELINE_STATUSES = ["received", "processing", "scored", "refused", "failed"] as const;
const EMPTY_JOBS: JobListItem[] = [];

const EMPTY_COUNTS: ApplicationCounts = {
  received: 0,
  processing: 0,
  scored: 0,
  refused: 0,
  failed: 0,
};

function sumCounts(jobs: JobListItem[]): ApplicationCounts {
  return jobs.reduce(
    (acc, job) => ({
      received: acc.received + job.application_counts.received,
      processing: acc.processing + job.application_counts.processing,
      scored: acc.scored + job.application_counts.scored,
      refused: acc.refused + job.application_counts.refused,
      failed: acc.failed + job.application_counts.failed,
    }),
    EMPTY_COUNTS,
  );
}

function formatCreatedAt(iso: string): string {
  return new Intl.DateTimeFormat(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(iso));
}

function PipelineChip({
  status,
  count,
}: {
  status: (typeof PIPELINE_STATUSES)[number];
  count: number;
}) {
  const failed = status === "failed";
  const processing = status === "processing";
  const label = status.charAt(0).toUpperCase() + status.slice(1);

  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-lg border px-3 py-1.5",
        failed
          ? "border-error/20 bg-error-container/40"
          : "border-outline-variant bg-surface-container-low",
        processing && "border-secondary/30",
      )}
    >
      {processing ? <span className="size-1.5 rounded-full bg-secondary" /> : null}
      <span
        className={cn(
          "text-label-sm text-on-surface-variant",
          failed && "text-error",
          processing && "font-medium text-secondary",
        )}
      >
        {label}
      </span>
      <span
        className={cn(
          "text-label-md font-semibold text-on-surface",
          failed && "text-error",
          processing && "text-secondary",
        )}
      >
        {count}
      </span>
    </div>
  );
}

function CreateJobButton({ className }: { className?: string }) {
  return (
    <Link
      className={cn(
        "inline-flex items-center justify-center gap-space-xs rounded-lg border border-transparent bg-primary px-space-md py-2.5 text-label-lg text-on-primary",
        "hover:bg-inverse-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary focus-visible:ring-offset-2",
        className,
      )}
      href="/jobs/new"
    >
      <Icon className="text-[18px]" name="add" />
      Create Job
    </Link>
  );
}

export function JobsList() {
  const jobsQuery = useJobs();
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [copyError, setCopyError] = useState(false);

  const jobs = jobsQuery.data ?? EMPTY_JOBS;
  const openCount = jobs.filter((job) => job.status === "open").length;
  const closedCount = jobs.filter((job) => job.status === "closed").length;
  const totals = sumCounts(jobs);

  const visibleJobs = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return jobs.filter((job) => {
      if (statusFilter !== "all" && job.status !== statusFilter) {
        return false;
      }
      if (!needle) {
        return true;
      }
      return (
        job.title.toLowerCase().includes(needle) || job.public_slug.toLowerCase().includes(needle)
      );
    });
  }, [jobs, query, statusFilter]);

  async function copyLink(job: JobListItem) {
    setCopyError(false);
    try {
      await navigator.clipboard.writeText(job.public_url);
      setCopiedId(job.id);
      window.setTimeout(() => {
        setCopiedId((current) => (current === job.id ? null : current));
      }, 1500);
    } catch {
      setCopyError(true);
    }
  }

  if (jobsQuery.isPending) {
    return <p className="text-body-md text-on-surface-variant">Loading…</p>;
  }

  if (jobsQuery.isError) {
    return <AuthErrorBanner message={getApiErrorMessage(jobsQuery.error)} />;
  }

  return (
    <div className="flex flex-col gap-space-lg">
      <div className="flex flex-col justify-between gap-space-md pb-space-xs sm:flex-row sm:items-center">
        <div>
          <h1 className="text-headline-xl text-on-surface">Job Postings</h1>
          <p className="mt-1 max-w-3xl text-body-md text-on-surface-variant">
            Manage active screening pipelines, copy candidate application links, and monitor
            real-time applicant metrics.
          </p>
        </div>
        <CreateJobButton />
      </div>

      <div className="grid grid-cols-2 gap-space-md md:grid-cols-3 lg:grid-cols-6">
        <MetricCard icon="work" label="Open jobs" value={openCount} />
        <MetricCard icon="inbox" label="Received" value={totals.received} />
        <MetricCard icon="sync" label="Processing" value={totals.processing} />
        <MetricCard icon="fact_check" label="Scored" value={totals.scored} />
        <MetricCard icon="block" label="Refused" value={totals.refused} />
        <MetricCard icon="error" label="Failed" value={totals.failed} />
      </div>

      {jobs.length === 0 ? (
        <div className="flex flex-col items-start gap-space-md rounded-xl border border-outline-variant bg-surface-container-lowest p-space-lg shadow-sm">
          <p className="text-body-md text-on-surface-variant">
            No jobs yet. Create a posting to generate a public apply link.
          </p>
          <CreateJobButton />
        </div>
      ) : (
        <>
          <div className="flex flex-col items-stretch justify-between gap-space-md rounded-xl border border-outline-variant bg-surface-container-lowest p-space-md shadow-sm md:flex-row md:items-center">
            <div className="relative max-w-md flex-1">
              <Icon
                className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-[18px] text-on-surface-variant"
                name="search"
              />
              <input
                className="w-full rounded-lg border border-outline-variant bg-surface-container-lowest py-2 pr-space-md pl-9 text-body-md text-on-surface outline-none placeholder:text-outline focus:border-secondary focus:ring-1 focus:ring-secondary"
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search by job title or apply slug"
                type="search"
                value={query}
              />
            </div>
            <div className="flex items-center rounded-lg border border-outline-variant bg-surface-container-low p-1">
              <FilterPill
                active={statusFilter === "all"}
                count={jobs.length}
                label="All"
                onClick={() => setStatusFilter("all")}
              />
              <FilterPill
                active={statusFilter === "open"}
                count={openCount}
                label="Open"
                onClick={() => setStatusFilter("open")}
              />
              <FilterPill
                active={statusFilter === "closed"}
                count={closedCount}
                label="Closed"
                onClick={() => setStatusFilter("closed")}
              />
            </div>
          </div>

          {copyError ? <AuthErrorBanner message="Could not copy the apply link." /> : null}

          {visibleJobs.length === 0 ? (
            <p className="text-body-md text-on-surface-variant">No matching jobs.</p>
          ) : (
            <div className="flex flex-col gap-space-md">
              {visibleJobs.map((job) => {
                const closed = job.status === "closed";
                return (
                  <article
                    className={cn(
                      "rounded-xl border p-space-lg shadow-sm",
                      closed
                        ? "border-outline-variant/80 bg-surface-container-low/70"
                        : "border-outline-variant bg-surface-container-lowest",
                    )}
                    key={job.id}
                  >
                    <div className="flex flex-col justify-between gap-space-md lg:flex-row lg:items-start">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-space-sm">
                          <h2
                            className={cn(
                              "text-headline-md",
                              closed ? "text-on-surface-variant" : "text-on-surface",
                            )}
                          >
                            {job.title}
                          </h2>
                          <Badge variant={job.status} />
                        </div>
                        <p className="mt-1.5 flex items-center gap-1 text-body-sm text-on-surface-variant">
                          <Icon className="text-[15px]" name="schedule" />
                          Created {formatCreatedAt(job.created_at)}
                        </p>
                        {closed ? (
                          <p className="mt-space-md text-body-sm text-on-surface-variant">
                            No longer accepting applications.
                          </p>
                        ) : null}
                        <div className="mt-space-md flex max-w-2xl flex-wrap items-center gap-space-sm rounded-lg border border-outline-variant bg-surface-container-low px-space-md py-2">
                          <Icon className="text-[16px] text-secondary" name="link" />
                          <span className="text-label-sm text-on-surface-variant">
                            Public apply link:
                          </span>
                          <span className="min-w-0 flex-1 truncate font-mono text-[12px] text-on-surface">
                            {job.public_url}
                          </span>
                          <Button
                            className="px-2.5 py-1 text-label-sm"
                            onClick={() => void copyLink(job)}
                            type="button"
                            variant="outline"
                          >
                            <Icon className="text-[14px]" name="content_copy" />
                            {copiedId === job.id ? "Copied" : "Copy Link"}
                          </Button>
                        </div>
                      </div>
                      <Link
                        className="inline-flex items-center gap-1.5 self-start rounded-lg bg-secondary px-space-md py-2 text-label-md font-medium text-on-secondary hover:bg-on-secondary-container lg:self-center"
                        href={`/jobs/${job.id}`}
                      >
                        View Dashboard
                        <Icon className="text-[16px]" name="arrow_forward" />
                      </Link>
                    </div>
                    <div className="mt-space-lg flex flex-wrap items-center gap-space-sm border-t border-outline-variant pt-space-md">
                      <span className="mr-1 text-label-sm font-semibold tracking-wider text-on-surface-variant uppercase">
                        Pipeline
                      </span>
                      {PIPELINE_STATUSES.map((status) => (
                        <PipelineChip
                          count={job.application_counts[status]}
                          key={status}
                          status={status}
                        />
                      ))}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function MetricCard({ icon, label, value }: { icon: string; label: string; value: number }) {
  return (
    <div className="flex flex-col justify-between rounded-xl border border-outline-variant bg-surface-container-lowest p-space-md shadow-sm">
      <div className="flex items-center justify-between">
        <span className="text-label-md text-on-surface-variant">{label}</span>
        <Icon className="text-[20px] text-secondary" name={icon} />
      </div>
      <span className="mt-space-md text-headline-xl font-semibold text-on-surface">{value}</span>
    </div>
  );
}

function FilterPill({
  active,
  count,
  label,
  onClick,
}: {
  active: boolean;
  count: number;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      className={cn(
        "rounded px-space-md py-1 text-label-md transition-colors",
        active
          ? "bg-surface-container-lowest font-semibold text-on-surface shadow-sm"
          : "text-on-surface-variant hover:text-on-surface",
      )}
      onClick={onClick}
      type="button"
    >
      {label} <span className="font-normal text-on-surface-variant">({count})</span>
    </button>
  );
}
