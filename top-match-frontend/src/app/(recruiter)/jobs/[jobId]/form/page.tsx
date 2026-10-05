import { JobFormPage } from "@/components/jobs/job-form-page";

export default async function JobFormRoute({ params }: { params: Promise<{ jobId: string }> }) {
  const { jobId } = await params;
  return <JobFormPage jobId={jobId} />;
}
