import { Icon } from "@/components/icon";

/** The job's must conditions, shown to candidates before they fill in the form. */
export function BeforeYouApply({ items }: { items: string[] }) {
  if (items.length === 0) {
    return null;
  }
  return (
    <section
      aria-labelledby="before-you-apply-heading"
      className="rounded-lg border border-outline-variant bg-surface-container-lowest p-space-md shadow-sm"
    >
      <h2
        className="mb-2 flex items-center gap-2 text-label-lg font-semibold text-on-surface"
        id="before-you-apply-heading"
      >
        <Icon className="text-[18px] text-secondary" name="checklist" />
        Before you apply
      </h2>
      <p className="mb-2 text-body-sm text-on-surface-variant">
        This role requires the following. You will be asked about each one on the form.
      </p>
      <ul className="flex list-disc flex-col gap-1 pl-5 text-body-sm text-on-surface">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
