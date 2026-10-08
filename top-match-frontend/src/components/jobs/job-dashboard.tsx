"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

import { AuthErrorBanner } from "@/components/auth/auth-error-banner";
import { Icon } from "@/components/icon";
import { JobCloseDialog } from "@/components/jobs/job-close-dialog";
import { JobEditPanel } from "@/components/jobs/job-edit-panel";
import { LeaderboardTable } from "@/components/jobs/leaderboard-table";
import { UnscoredLists } from "@/components/jobs/unscored-lists";
import { Badge } from "@/components/ui/badge";
import { Banner } from "@/components/ui/banner";
import { Button } from "@/components/ui/button";
import { useExportJob, useJob, useLeaderboard } from "@/hooks/use-jobs";
import { getApiErrorMessage, isNotFoundError } from "@/lib/api-error";
import { cn } from "@/lib/cn";
import { csvFilenameFromTitle, downloadTextFile } from "@/lib/download";
import {
  PHASE_LABEL,
  SCREENING_PHASES,
  STATUS_LABEL,
  type ApplicationStatus,
  type LeaderboardQuery,
  type ScreeningPhase,
} from "@/types/applications";
import { EMPTY_COUNTS, totalApplications } from "@/types/jobs";

const PIPELINE_STATUSES: ApplicationStatus[] = [
  "received",
  "processing",
  "scored",
  "knocked_out",
  "refused",
  "failed",
];

// Default view. Knocked-out, refused and failed applicants have their own lists below.
const ACTIVE_STATUSES: ApplicationStatus[] = ["received", "processing", "scored"];
const ALL_STATUSES = "all";

type StatusFilter = ApplicationStatus | typeof ALL_STATUSES | undefined;

const COUNT_CARDS: Array<{
  status: ApplicationStatus;
  icon: string;
}> = [
  { status: "received", icon: "inbox" },
  { status: "processing", icon: "sync" },
  { status: "scored", icon: "verified" },
  { status: "knocked_out", icon: "filter_alt_off" },
  { status: "refused", icon: "do_not_disturb_on" },
  { status: "failed", icon: "error_outline" },
];

const DEFAULT_LIMIT = 50;
const MIN_LIMIT = 1;
const MAX_LIMIT = 100;
const MIN_TOP_N = 1;
const MAX_TOP_N = 500;
function parseLimit(raw: string | null): number {
  const value = Number(raw);
  if (!Number.isInteger(value)) {
    return DEFAULT_LIMIT;
  }
  return Math.min(MAX_LIMIT, Math.max(MIN_LIMIT, value));
}

function parseOffset(raw: string | null): number {
  const value = Number(raw);
  if (!Number.isInteger(value) || value < 0) {
    return 0;
  }
  return value;
}

function parseStatus(raw: string | null): StatusFilter {
  if (raw === ALL_STATUSES) {
    return ALL_STATUSES;
  }
  if (raw && (PIPELINE_STATUSES as string[]).includes(raw)) {
    return raw as ApplicationStatus;
  }
  return undefined;
}

function parseStage(raw: string | null): ScreeningPhase | undefined {
  if (raw && (SCREENING_PHASES as string[]).includes(raw)) {
    return raw as ScreeningPhase;
  }
  return undefined;
}

export function JobDashboard({ jobId }: { jobId: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const status = parseStatus(searchParams.get("status"));
  const stage = parseStage(searchParams.get("stage"));
  const limit = parseLimit(searchParams.get("limit"));
  const offset = parseOffset(searchParams.get("offset"));

  const query = useMemo<LeaderboardQuery>(() => {
    const next: LeaderboardQuery = { limit, offset };
    if (status === undefined) {
      next.status = ACTIVE_STATUSES;
    } else if (status !== ALL_STATUSES) {
      next.status = status;
    }
    if (stage) {
      next.stage = stage;
    }
    return next;
  }, [limit, offset, status, stage]);

  const jobQuery = useJob(jobId);
  const leaderboardQuery = useLeaderboard(jobId, query);
  const exportJob = useExportJob(jobId);

  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [closeOpen, setCloseOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [exportMode, setExportMode] = useState<"top_n" | "selected">("top_n");
  const [topN, setTopN] = useState("25");
  const [actionError, setActionError] = useState("");

  const job = jobQuery.data;
  const leaderboard = leaderboardQuery.data;
  const counts = leaderboard?.counts ?? job?.application_counts ?? EMPTY_COUNTS;
  const items = leaderboard?.items ?? [];
  const total = leaderboard?.total ?? 0;
  const allCount = totalApplications(counts);
  const activeCount = counts.received + counts.processing + counts.scored;
  const selectedCount = selectedIds.size;

  function replaceQuery(next: {
    status?: StatusFilter;
    stage?: ScreeningPhase;
    limit: number;
    offset: number;
  }) {
    const params = new URLSearchParams();
    if (next.status) {
      params.set("status", next.status);
    }
    if (next.stage) {
      params.set("stage", next.stage);
    }
    if (next.limit !== DEFAULT_LIMIT) {
      params.set("limit", String(next.limit));
    }
    if (next.offset > 0) {
      params.set("offset", String(next.offset));
    }
    const qs = params.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
  }

  async function copyLink() {
    if (!job) {
      return;
    }
    setCopyError(false);
    setActionError("");
    try {
      await navigator.clipboard.writeText(job.public_url);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopyError(true);
    }
  }

  function onFilterChange(value: string) {
    setSelectedIds(new Set());
    replaceQuery({
      status: parseStatus(value),
      stage,
      limit,
      offset: 0,
    });
  }

  function onStageChange(value: string) {
    setSelectedIds(new Set());
    replaceQuery({ status, stage: parseStage(value), limit, offset: 0 });
  }

  function onPrevious() {
    replaceQuery({ status, stage, limit, offset: Math.max(0, offset - limit) });
  }

  function onNext() {
    replaceQuery({ status, stage, limit, offset: offset + limit });
  }

  function onToggle(id: string) {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  function onToggleAll(checked: boolean) {
    setSelectedIds((current) => {
      const next = new Set(current);
      for (const item of items) {
        if (checked) {
          next.add(item.id);
        } else {
          next.delete(item.id);
        }
      }
      return next;
    });
  }

  async function onExport() {
    setActionError("");
    try {
      const csv =
        exportMode === "top_n"
          ? await exportJob.mutateAsync({
              top_n: Math.min(
                MAX_TOP_N,
                Math.max(MIN_TOP_N, Number.parseInt(topN, 10) || MIN_TOP_N),
              ),
            })
          : await exportJob.mutateAsync({ application_ids: Array.from(selectedIds) });
      downloadTextFile(csv, csvFilenameFromTitle(job?.title ?? "job"));
    } catch (error) {
      setActionError(getApiErrorMessage(error));
    }
  }

  if (jobQuery.isPending) {
    return <p className="text-body-md text-on-surface-variant">Loading…</p>;
  }

  if (jobQuery.isError || !job) {
    if (jobQuery.error && isNotFoundError(jobQuery.error)) {
      return (
        <div className="flex flex-col gap-space-md">
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
    return <AuthErrorBanner message={getApiErrorMessage(jobQuery.error)} />;
  }

  const exportDisabled =
    exportJob.isPending || (exportMode === "selected" && selectedCount === 0);
  const showEmpty = leaderboard && total === 0 && allCount === 0;
  const showFilteredEmpty = leaderboard && total === 0 && allCount > 0;

  return (
    <div className="flex flex-col gap-space-lg">
      {job.screening_disclaimer ? <Banner>{job.screening_disclaimer}</Banner> : null}
      {job.form_warnings.length > 0 ? (
        <Banner>
          <span className="font-semibold">Check your knockout questions. </span>
          {job.form_warnings.map((warning) => warning.message).join(" ")}
        </Banner>
      ) : null}

      <div className="flex flex-col gap-space-md">
        <nav className="flex items-center gap-space-xs text-label-sm text-on-surface-variant">
          <Link className="hover:text-secondary hover:underline" href="/jobs">
            Jobs
          </Link>
          <Icon className="text-[14px]" name="chevron_right" />
          <span className="font-semibold text-on-surface">{job.title}</span>
        </nav>

        <div className="flex flex-col justify-between gap-space-md pb-space-xs lg:flex-row lg:items-center">
          <div className="flex flex-wrap items-center gap-space-md">
            <h1 className="text-headline-xl tracking-tight text-on-surface">{job.title}</h1>
            <Badge variant={job.status} />
          </div>
          <div className="flex flex-wrap items-center gap-space-sm">
            <Button onClick={() => setEditOpen(true)} type="button" variant="outline">
              <Icon className="text-on-surface-variant" name="edit" />
              Edit Job
            </Button>
            <Button onClick={() => router.push(`/jobs/${jobId}/form`)} type="button" variant="outline">
              <Icon className="text-on-surface-variant" name="edit_note" />
              Application Form
            </Button>
            {job.status === "open" ? (
              <Button onClick={() => setCloseOpen(true)} type="button" variant="destructive">
                <Icon name="block" />
                Close Job
              </Button>
            ) : null}
          </div>
        </div>

        {copyError ? <AuthErrorBanner message="Could not copy the apply link." /> : null}
        {actionError ? <AuthErrorBanner message={actionError} /> : null}

        <div className="flex flex-col justify-between gap-space-sm rounded-xl border border-outline-variant bg-surface-container-lowest p-space-sm px-space-md shadow-sm sm:flex-row sm:items-center">
          <div className="flex min-w-0 items-center gap-space-sm">
            <Icon className="shrink-0 text-on-surface-variant" name="link" />
            <span className="shrink-0 text-label-sm font-semibold text-on-surface-variant">
              Public candidate link:
            </span>
            <span className="truncate font-mono text-body-sm text-on-surface">{job.public_url}</span>
          </div>
          <Button className="shrink-0 py-1 text-label-sm" onClick={() => void copyLink()}>
            <Icon className="text-[16px]" name="content_copy" />
            {copied ? "Copied" : "Copy apply link"}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-space-sm sm:grid-cols-3 lg:grid-cols-6">
        {COUNT_CARDS.map((card) => {
          const failed = card.status === "failed";
          const processing = card.status === "processing";
          return (
            <div
              className="flex flex-col justify-between rounded-xl border border-outline-variant bg-surface-container-lowest p-space-md shadow-sm"
              key={card.status}
            >
              <div className="flex items-center justify-between">
                <span
                  className={cn(
                    "text-label-sm font-semibold tracking-wider uppercase",
                    failed ? "text-error" : processing ? "text-secondary" : "text-on-surface-variant",
                  )}
                >
                  {STATUS_LABEL[card.status]}
                </span>
                <Icon
                  className={cn(
                    "text-[20px]",
                    failed ? "text-error" : processing ? "text-secondary" : "text-on-surface-variant",
                  )}
                  name={card.icon}
                />
              </div>
              <span
                className={cn(
                  "mt-space-xs text-headline-lg font-bold",
                  failed ? "text-error" : "text-on-surface",
                )}
              >
                {counts[card.status]}
              </span>
            </div>
          );
        })}
      </div>

      <div className="flex flex-col justify-between gap-space-md rounded-xl border border-outline-variant bg-surface-container-lowest p-space-md shadow-sm md:flex-row md:items-center">
        <div className="flex flex-wrap items-center gap-space-md">
          <div className="flex items-center gap-space-xs">
            <label
              className="text-label-sm font-semibold text-on-surface-variant"
              htmlFor="status-filter"
            >
              Filter:
            </label>
            <select
              className="rounded-lg border border-outline-variant bg-surface-container-lowest px-2.5 py-1.5 text-label-md text-on-surface focus:border-secondary focus:ring-0"
              id="status-filter"
              onChange={(event) => onFilterChange(event.target.value)}
              value={status ?? ""}
            >
              <option value="">Active &amp; scored ({activeCount})</option>
              <option value={ALL_STATUSES}>All statuses ({allCount})</option>
              {PIPELINE_STATUSES.map((value) => (
                <option key={value} value={value}>
                  {STATUS_LABEL[value]} ({counts[value]})
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-space-xs">
            <label
              className="text-label-sm font-semibold text-on-surface-variant"
              htmlFor="stage-filter"
            >
              Stage:
            </label>
            <select
              className="rounded-lg border border-outline-variant bg-surface-container-lowest px-2.5 py-1.5 text-label-md text-on-surface focus:border-secondary focus:ring-0"
              id="stage-filter"
              onChange={(event) => onStageChange(event.target.value)}
              value={stage ?? ""}
            >
              <option value="">All stages</option>
              {SCREENING_PHASES.map((value) => (
                <option key={value} value={value}>
                  {PHASE_LABEL[value]}
                </option>
              ))}
            </select>
          </div>
          <div className="hidden h-4 w-px bg-outline-variant sm:block" />
          <div className="flex items-center gap-2 rounded-full border border-outline-variant/60 bg-surface px-2.5 py-1">
            <span className="relative flex size-2">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-secondary opacity-75" />
              <span className="relative inline-flex size-2 rounded-full bg-secondary" />
            </span>
            <span className="text-label-sm font-medium text-on-surface-variant">
              Updates every 3s
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-space-md">
          <div className="flex items-center gap-space-sm text-label-sm text-on-surface">
            <label className="flex cursor-pointer items-center gap-1.5">
              <input
                checked={exportMode === "top_n"}
                className="size-3.5 border-outline"
                name="export-mode"
                onChange={() => setExportMode("top_n")}
                type="radio"
              />
              <span>Top N</span>
            </label>
            <input
              className="w-16 rounded-lg border border-outline-variant px-1.5 py-1 text-center font-mono text-label-sm focus:border-secondary focus:ring-0"
              disabled={exportMode !== "top_n"}
              max={MAX_TOP_N}
              min={MIN_TOP_N}
              onChange={(event) => setTopN(event.target.value)}
              type="number"
              value={topN}
            />
            <span className="mx-1 text-outline-variant">|</span>
            <label className="flex cursor-pointer items-center gap-1.5">
              <input
                checked={exportMode === "selected"}
                className="size-3.5 border-outline"
                name="export-mode"
                onChange={() => setExportMode("selected")}
                type="radio"
              />
              <span>
                Selected (<span className="font-bold text-secondary">{selectedCount}</span>)
              </span>
            </label>
          </div>
          <div className="group relative">
            <Button
              className="py-1.5 text-label-sm"
              disabled={exportDisabled}
              onClick={() => void onExport()}
              pending={exportJob.isPending}
              type="button"
              variant="outline"
            >
              <Icon name="download" />
              Download CSV
              <Icon className="text-[14px] text-on-surface-variant" name="help_outline" />
            </Button>
            <div className="absolute right-0 bottom-full z-40 mb-2 hidden w-64 rounded-lg bg-inverse-surface p-space-sm text-label-sm text-inverse-on-surface shadow-xl group-hover:block">
              First row of the file is the screening disclaimer.
            </div>
          </div>
        </div>
      </div>

      {leaderboardQuery.isError ? (
        <AuthErrorBanner message={getApiErrorMessage(leaderboardQuery.error)} />
      ) : leaderboardQuery.isPending && !leaderboard ? (
        <p className="text-body-md text-on-surface-variant">Loading applications…</p>
      ) : showEmpty ? (
        <div className="flex min-h-[380px] flex-col items-center justify-center rounded-xl border border-outline-variant bg-surface-container-lowest p-space-xl text-center shadow-sm">
          <div className="mb-space-md flex size-14 items-center justify-center rounded-full bg-surface-container text-on-surface-variant">
            <Icon className="text-[28px]" name="person_search" />
          </div>
          <h2 className="mb-space-xs text-headline-md font-semibold text-on-surface">
            No applications yet
          </h2>
          <p className="mb-space-lg max-w-md text-body-md text-on-surface-variant">
            Share the public apply link to start screening candidates against this job&apos;s
            requirements.
          </p>
          <Button onClick={() => void copyLink()} type="button">
            <Icon name="share" />
            Share the apply link
          </Button>
        </div>
      ) : showFilteredEmpty ? (
        <p className="text-body-md text-on-surface-variant">No applications match these filters.</p>
      ) : (
        <LeaderboardTable
          items={items}
          jobId={jobId}
          limit={limit}
          offset={offset}
          onNext={onNext}
          onPrevious={onPrevious}
          onRescoreError={setActionError}
          onToggle={onToggle}
          onToggleAll={onToggleAll}
          selectedIds={selectedIds}
          total={total}
        />
      )}

      <UnscoredLists counts={counts} jobId={jobId} onError={setActionError} />

      {editOpen ? <JobEditPanel job={job} onClose={() => setEditOpen(false)} /> : null}
      {closeOpen ? <JobCloseDialog jobId={jobId} onClose={() => setCloseOpen(false)} /> : null}
    </div>
  );
}
