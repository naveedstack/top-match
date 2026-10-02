import { api } from "@/lib/api";
import type {
  ApplicationAccepted,
  ApplicationCreateRequest,
  ApplicationDetail,
  ResumeUploaded,
} from "@/types/applications";

export async function uploadResume(file: Blob): Promise<ResumeUploaded> {
  const { data } = await api.post<ResumeUploaded>("/public/files", file, {
    headers: { "Content-Type": "application/pdf" },
  });
  return data;
}

export async function applyToJob(
  slug: string,
  body: ApplicationCreateRequest,
): Promise<ApplicationAccepted> {
  const { data } = await api.post<ApplicationAccepted>(
    `/public/jobs/${slug}/applications`,
    body,
  );
  return data;
}

export async function getApplication(applicationId: string): Promise<ApplicationDetail> {
  const { data } = await api.get<ApplicationDetail>(`/applications/${applicationId}`);
  return data;
}

export async function rescoreApplication(applicationId: string): Promise<ApplicationAccepted> {
  const { data } = await api.post<ApplicationAccepted>(
    `/applications/${applicationId}/rescore`,
  );
  return data;
}
