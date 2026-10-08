import { Icon } from "@/components/icon";
import { cn } from "@/lib/cn";
import { IMPORTANCE_LABEL } from "@/lib/condition-presets";
import type { ConditionVerdict as Verdict, JobCondition } from "@/types/forms";

const VERDICT: Record<Verdict, { label: string; icon: string; className: string }> = {
  pass: { label: "Met", icon: "check_circle", className: "text-status-scored" },
  partial: { label: "Partly met", icon: "contrast", className: "text-status-processing" },
  fail: { label: "Not met", icon: "cancel", className: "text-error" },
  not_scored: { label: "Not scored", icon: "info", className: "text-on-surface-variant" },
};

function formatSalary(condition: JobCondition): string {
  const salary = condition.salary;
  if (!salary) {
    return "";
  }
  const format = (value: number) => value.toLocaleString();
  return `Range ${salary.currency} ${format(salary.min)}–${format(salary.max)}`;
}

/** Importance and outcome of one job-condition answer. */
export function ConditionVerdict({
  condition,
  verdict,
}: {
  condition: JobCondition;
  verdict: Verdict;
}) {
  const outcome = VERDICT[verdict];
  const salary = formatSalary(condition);
  return (
    <span className="mt-1 flex flex-wrap items-center gap-2 text-label-sm">
      <span className="rounded border border-outline-variant bg-surface-container-low px-1.5 py-0.5 font-semibold text-on-surface">
        {IMPORTANCE_LABEL[condition.importance]}
      </span>
      <span className={cn("inline-flex items-center gap-1 font-medium", outcome.className)}>
        <Icon className="text-[15px]" name={outcome.icon} />
        {outcome.label}
      </span>
      {salary ? <span className="text-on-surface-variant">{salary}</span> : null}
    </span>
  );
}
