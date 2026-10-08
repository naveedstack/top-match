"use client";

import Link from "next/link";
import type { MouseEvent } from "react";

import type { ApplicationAction } from "@/api/applications";
import { Icon } from "@/components/icon";
import { useApplicationAction } from "@/hooks/use-applications";
import { useLeaderboard } from "@/hooks/use-jobs";
import { getApiErrorMessage } from "@/lib/api-error";
import { cn } from "@/lib/cn";
import { stageLabel, type ApplicationStatus, type LeaderboardItem } from "@/types/applications";
import type { ApplicationCounts } from "@/types/jobs";

const LIST_LIMIT = 100;

type ListConfig = {
  key: string;
  title: string;
  description: string;
  icon: string;
  open: boolean;
  actions: Array<{ action: ApplicationAction; label: string; pendingLabel: string }>;
  filter?: (item: LeaderboardItem) => boolean;
};

const RETRY = { action: "rescore", label: "Retry", pendingLabel: "Retrying…" } as const;
const REVIEWED = {
  action: "mark-reviewed",
  label: "Mark reviewed",
  pendingLabel: "Saving…",
} as const;

const KNOCKED_OUT: ListConfig = {
  key: "knocked_out",
  title: "Knocked out",
  description: "Failed a knockout question. Their resume was not sent to the model.",
  icon: "filter_alt_off",
  open: false,
  actions: [{ action: "move-forward", label: "Move forward anyway", pendingLabel: "Moving…" }],
};

const REFUSED: ListConfig = {
  key: "refused",
  title: "Refused",
  description: "The file was read but was not recognized as a resume.",
  icon: "do_not_disturb_on",
  open: true,
  actions: [RETRY, REVIEWED],
};

const UNREADABLE: ListConfig = {
  key: "unreadable",
  title: "Unreadable",
  description: "No usable text could be read from the PDF.",
  icon: "visibility_off",
  open: true,
  actions: [RETRY, REVIEWED],
  filter: (item) => item.stop_code === "unreadable",
};

const FAILED: ListConfig = {
  key: "failed",
  title: "Failed",
  description: "Scoring did not finish. Retry, or review the application yourself.",
  icon: "error_outline",
  open: true,
  actions: [RETRY, REVIEWED],
  filter: (item) => item.stop_code !== "unreadable",
};

export function UnscoredLists({
  jobId,
  counts,
  onError,
}: {
  jobId: string;
  counts: ApplicationCounts;
  onError: (message: string) => void;
}) {
  const knockedOut = useStatusList(jobId, "knocked_out", counts.knocked_out);
  const refused = useStatusList(jobId, "refused", counts.refused);
  const failed = useStatusList(jobId, "failed", counts.failed);

  if (counts.knocked_out + counts.refused + counts.failed === 0) {
    return null;
  }

  return (
    <section className="flex flex-col gap-space-sm">
      <div>
        <h2 className="text-headline-sm font-semibold text-on-surface">Not scored</h2>
        <p className="text-body-sm text-on-surface-variant">
          Applicants who were stopped before a score. Nobody is removed automatically.
        </p>
      </div>
      <UnscoredList config={KNOCKED_OUT} items={knockedOut} jobId={jobId} onError={onError} />
      <UnscoredList config={REFUSED} items={refused} jobId={jobId} onError={onError} />
      <UnscoredList config={UNREADABLE} items={failed} jobId={jobId} onError={onError} />
      <UnscoredList config={FAILED} items={failed} jobId={jobId} onError={onError} />
    </section>
  );
}

function useStatusList(
  jobId: string,
  status: ApplicationStatus,
  count: number,
): LeaderboardItem[] {
  const query = useLeaderboard(jobId, { status, limit: LIST_LIMIT }, { enabled: count > 0 });
  return count > 0 ? (query.data?.items ?? []) : [];
}

function UnscoredList({
  config,
  items,
  jobId,
  onError,
}: {
  config: ListConfig;
  items: LeaderboardItem[];
  jobId: string;
  onError: (message: string) => void;
}) {
  const rows = config.filter ? items.filter(config.filter) : items;
  if (rows.length === 0) {
    return null;
  }

  return (
    <details
      className="group overflow-hidden rounded-xl border border-outline-variant bg-surface-container-lowest shadow-sm"
      open={config.open}
    >
      <summary className="flex cursor-pointer list-none items-center justify-between gap-space-sm px-space-md py-3 hover:bg-surface-container-low/50">
        <span className="flex items-center gap-2">
          <Icon className="text-[18px] text-on-surface-variant" name={config.icon} />
          <span className="text-label-lg font-semibold text-on-surface">{config.title}</span>
          <span className="rounded-full bg-surface-container px-2 py-0.5 text-label-sm text-on-surface-variant">
            {rows.length}
          </span>
          <span className="hidden text-body-sm text-on-surface-variant md:inline">
            {config.description}
          </span>
        </span>
        <Icon
          className="text-[18px] text-on-surface-variant transition-transform group-open:rotate-180"
          name="expand_more"
        />
      </summary>
      <ul className="divide-y divide-outline-variant/60 border-t border-outline-variant">
        {rows.map((item) => (
          <li
            className="flex flex-col gap-2 px-space-md py-3 sm:flex-row sm:items-center sm:justify-between"
            key={item.id}
          >
            <div className="min-w-0">
              <Link
                className="font-semibold text-on-surface hover:text-secondary hover:underline"
                href={`/jobs/${jobId}/applications/${item.id}`}
              >
                {item.email}
              </Link>
              <p className="text-body-sm text-on-surface-variant">
                <span className="font-medium">{stageLabel(item)}</span>
                {item.stop_reason ? ` · ${item.stop_reason}` : null}
                {item.reviewed_at ? " · Reviewed" : null}
              </p>
            </div>
            <div className="flex shrink-0 flex-wrap gap-2">
              {config.actions.map((action) =>
                action.action === "mark-reviewed" && item.reviewed_at ? null : (
                  <ActionButton
                    action={action}
                    applicationId={item.id}
                    jobId={jobId}
                    key={action.action}
                    onError={onError}
                  />
                ),
              )}
            </div>
          </li>
        ))}
      </ul>
    </details>
  );
}

export function ActionButton({
  jobId,
  applicationId,
  action,
  onError,
}: {
  jobId: string;
  applicationId: string;
  action: ListConfig["actions"][number];
  onError: (message: string) => void;
}) {
  const mutation = useApplicationAction(jobId, applicationId, action.action);

  function onClick(event: MouseEvent<HTMLButtonElement>) {
    event.stopPropagation();
    event.preventDefault();
    mutation.mutate(undefined, {
      onError: (error) => onError(getApiErrorMessage(error)),
    });
  }

  return (
    <button
      className={cn(
        "inline-flex items-center gap-1 rounded border border-outline-variant bg-surface px-2.5 py-1 text-label-sm font-medium text-on-surface",
        "hover:border-on-surface disabled:pointer-events-none disabled:opacity-50",
      )}
      disabled={mutation.isPending}
      onClick={onClick}
      type="button"
    >
      {mutation.isPending ? action.pendingLabel : action.label}
    </button>
  );
}
