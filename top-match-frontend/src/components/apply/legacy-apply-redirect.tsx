"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { usePublicJob } from "@/hooks/use-jobs";
import { isNotFoundError } from "@/lib/api-error";
import { applyPath } from "@/lib/apply-path";

export function LegacyApplyRedirect({
  slug,
  suffix = "",
}: {
  slug: string;
  suffix?: "" | "/done";
}) {
  const router = useRouter();
  const jobQuery = usePublicJob(slug);

  useEffect(() => {
    const companySlug = jobQuery.data?.company_slug;
    if (companySlug) {
      router.replace(`${applyPath(companySlug, slug)}${suffix}`);
    }
  }, [jobQuery.data, router, slug, suffix]);

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

  return <p className="text-body-md text-on-surface-variant">Loading…</p>;
}
