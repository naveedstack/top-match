import { ApplicationDetailView } from "@/components/applications/application-detail";

export default async function ApplicationPage({
  params,
}: {
  params: Promise<{ jobId: string; applicationId: string }>;
}) {
  const { jobId, applicationId } = await params;
  return <ApplicationDetailView applicationId={applicationId} jobId={jobId} />;
}
