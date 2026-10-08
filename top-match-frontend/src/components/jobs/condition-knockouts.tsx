import { Icon } from "@/components/icon";
import type { ConditionKnockoutCount } from "@/types/jobs";

/** How many applicants each must condition stopped, and how many were moved forward after. */
export function ConditionKnockouts({ items }: { items: ConditionKnockoutCount[] }) {
  if (items.length === 0) {
    return null;
  }
  return (
    <section className="rounded-xl border border-outline-variant bg-surface-container-lowest p-space-md shadow-sm">
      <h2 className="mb-space-sm flex items-center gap-2 text-headline-sm font-semibold text-on-surface">
        <Icon className="text-[20px] text-secondary" name="filter_alt" />
        Must conditions
      </h2>
      <ul className="flex flex-col divide-y divide-outline-variant">
        {items.map((item) => (
          <li
            className="flex flex-col gap-1 py-2 sm:flex-row sm:items-center sm:justify-between"
            key={item.field_id}
          >
            <span className="min-w-0 break-words text-body-md text-on-surface">{item.label}</span>
            <span className="shrink-0 text-label-md text-on-surface-variant">
              {item.stopped} stopped, {item.moved_forward} moved forward
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
