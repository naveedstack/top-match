import { Suspense } from "react";

import { JobDashboard } from "@/components/jobs/job-dashboard";

export default async function JobPage({ params }: { params: Promise<{ jobId: string }> }) {
  const { jobId } = await params;
  return (
    <Suspense fallback={<p className="text-body-md text-on-surface-variant">Loading…</p>}>
      <JobDashboard jobId={jobId} />
    </Suspense>
  );
}
