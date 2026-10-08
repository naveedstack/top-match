"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, type MouseEvent } from "react";

import { Icon } from "@/components/icon";
import { Badge } from "@/components/ui/badge";
import { useRescoreApplication } from "@/hooks/use-applications";
import { getApiErrorMessage } from "@/lib/api-error";
import { cn } from "@/lib/cn";
import { stageLabel, type LeaderboardItem } from "@/types/applications";

type LeaderboardTableProps = {
  items: LeaderboardItem[];
  total: number;
  offset: number;
  limit: number;
  jobId: string;
  selectedIds: Set<string>;
  onToggle: (id: string) => void;
  onToggleAll: (checked: boolean) => void;
  onPrevious: () => void;
  onNext: () => void;
  onRescoreError: (message: string) => void;
};

function formatAppliedAt(iso: string): string {
  return new Intl.DateTimeFormat(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(iso));
}

function formatScore(score: number | null): string {
  return score === null ? "—" : String(score);
}

export function LeaderboardTable({
  items,
  total,
  offset,
  limit,
  jobId,
  selectedIds,
  onToggle,
  onToggleAll,
  onPrevious,
  onNext,
  onRescoreError,
}: LeaderboardTableProps) {
  const router = useRouter();
  const selectAllRef = useRef<HTMLInputElement>(null);
  const pageIds = items.map((item) => item.id);
  const selectedOnPage = pageIds.filter((id) => selectedIds.has(id)).length;
  const allOnPageSelected = items.length > 0 && selectedOnPage === items.length;
  const someOnPageSelected = selectedOnPage > 0 && !allOnPageSelected;

  useEffect(() => {
    if (selectAllRef.current) {
      selectAllRef.current.indeterminate = someOnPageSelected;
    }
  }, [someOnPageSelected]);

  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + limit, total);
  const canPrevious = offset > 0;
  const canNext = offset + limit < total;

  function goToDetail(applicationId: string) {
    router.push(`/jobs/${jobId}/applications/${applicationId}`);
  }

  return (
    <div className="overflow-hidden rounded-xl border border-outline-variant bg-surface-container-lowest shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="h-10 border-b border-outline-variant bg-surface text-label-sm tracking-wider text-on-surface-variant uppercase">
              <th className="w-10 px-4 text-center">
                <input
                  aria-label="Select all on this page"
                  checked={allOnPageSelected}
                  className="size-4 rounded border-outline-variant"
                  onChange={(event) => onToggleAll(event.target.checked)}
                  ref={selectAllRef}
                  type="checkbox"
                />
              </th>
              <th className="px-4 py-2 font-semibold">Rank</th>
              <th className="px-4 py-2 font-semibold">Candidate Email</th>
              <th className="px-4 py-2 font-semibold">Status</th>
              <th className="px-4 py-2 font-semibold">Stage</th>
              <th className="px-4 py-2 font-semibold">Score</th>
              <th className="px-4 py-2 font-semibold">Flags</th>
              <th className="px-4 py-2 font-semibold">Applied</th>
              <th className="px-4 py-2 text-right font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant/60 text-body-sm">
            {items.map((item, index) => {
              const rank = offset + index + 1;
              const selected = selectedIds.has(item.id);
              return (
                <tr
                  className="h-[52px] cursor-pointer transition-colors duration-150 hover:bg-surface-container-low/50"
                  key={item.id}
                  onClick={() => goToDetail(item.id)}
                >
                  <td className="px-4 text-center" onClick={(event) => event.stopPropagation()}>
                    <input
                      aria-label={`Select ${item.email}`}
                      checked={selected}
                      className="size-4 rounded border-outline-variant"
                      onChange={() => onToggle(item.id)}
                      type="checkbox"
                    />
                  </td>
                  <td className="px-4 font-mono font-bold text-on-surface">#{rank}</td>
                  <td className="px-4 font-semibold text-on-surface">{item.email}</td>
                  <td className="px-4">
                    <Badge variant={item.status} />
                  </td>
                  <td
                    className={cn(
                      "px-4 text-label-md",
                      item.stopped_phase ? "text-error" : "text-on-surface-variant",
                    )}
                    title={item.stop_reason ?? undefined}
                  >
                    {stageLabel(item)}
                  </td>
                  <td className="px-4 font-mono text-headline-sm font-bold text-on-surface">
                    {formatScore(item.score)}
                  </td>
                  <td className="px-4">
                    {item.needs_review ? (
                      <span className="inline-flex items-center gap-1 rounded border border-amber-300 bg-amber-50 px-2 py-0.5 text-label-sm text-amber-800">
                        <Icon className="text-[15px] text-amber-700" name="warning" />
                        Needs review
                      </span>
                    ) : null}
                  </td>
                  <td className="px-4 text-label-md text-on-surface-variant">
                    {formatAppliedAt(item.created_at)}
                  </td>
                  <td className="px-4 text-right">
                    {item.status === "failed" ? (
                      <RescoreButton
                        applicationId={item.id}
                        jobId={jobId}
                        onError={onRescoreError}
                      />
                    ) : (
                      <Link
                        className="inline-flex rounded border border-outline-variant bg-surface px-2.5 py-1 text-label-sm text-on-surface hover:border-on-surface"
                        href={`/jobs/${jobId}/applications/${item.id}`}
                        onClick={(event) => event.stopPropagation()}
                      >
                        View
                      </Link>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="flex flex-col items-center justify-between gap-space-sm border-t border-outline-variant bg-surface px-space-md py-space-sm text-label-sm text-on-surface-variant sm:flex-row">
        <p>
          Showing{" "}
          <span className="font-semibold text-on-surface">
            {from}–{to}
          </span>{" "}
          of <span className="font-semibold text-on-surface">{total}</span>
        </p>
        <div className="flex items-center gap-1">
          <button
            className="rounded border border-outline-variant bg-surface-container-lowest px-2 py-1 text-on-surface hover:bg-surface-container-low disabled:cursor-not-allowed disabled:opacity-50"
            disabled={!canPrevious}
            onClick={onPrevious}
            type="button"
          >
            Previous
          </button>
          <button
            className="rounded border border-outline-variant bg-surface-container-lowest px-2 py-1 text-on-surface hover:bg-surface-container-low disabled:cursor-not-allowed disabled:opacity-50"
            disabled={!canNext}
            onClick={onNext}
            type="button"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

function RescoreButton({
  jobId,
  applicationId,
  onError,
}: {
  jobId: string;
  applicationId: string;
  onError: (message: string) => void;
}) {
  const rescore = useRescoreApplication(jobId, applicationId);

  function onClick(event: MouseEvent<HTMLButtonElement>) {
    event.stopPropagation();
    event.preventDefault();
    rescore.mutate(undefined, {
      onError: (error) => onError(getApiErrorMessage(error)),
    });
  }

  return (
    <button
      className={cn(
        "inline-flex items-center gap-1 rounded border border-error/40 bg-surface px-2.5 py-1 text-label-sm font-medium text-error",
        "hover:bg-error-container/40 disabled:pointer-events-none disabled:opacity-50",
      )}
      disabled={rescore.isPending}
      onClick={onClick}
      onMouseDown={(event) => event.stopPropagation()}
      type="button"
    >
      <Icon className="text-[14px]" name="refresh" />
      {rescore.isPending ? "Retrying…" : "Retry"}
    </button>
  );
}
