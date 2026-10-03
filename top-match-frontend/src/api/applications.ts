import { api } from "@/lib/api";
import type {
  ApplicationAccepted,
  ApplicationCreateRequest,
  ApplicationDetail,
  ResumeUploadUrlResponse,
  ResumeUploaded,
} from "@/types/applications";

function putHeaders(headers: Record<string, string>): Headers {
  const next = new Headers();
  for (const [name, value] of Object.entries(headers)) {
    if (name.toLowerCase() === "content-length") {
      continue;
    }
    next.set(name, value);
  }
  return next;
}

export async function uploadResume(file: Blob): Promise<ResumeUploaded> {
  const { data: signed } = await api.post<ResumeUploadUrlResponse>("/public/files/upload-url", {
    content_type: "application/pdf",
    byte_size: file.size,
  });
  const uploaded = await fetch(signed.upload_url, {
    method: "PUT",
    headers: putHeaders(signed.headers),
    body: file,
  });
  if (!uploaded.ok) {
    throw new Error("Could not upload resume");
  }
  const { data } = await api.post<ResumeUploaded>(`/public/files/${signed.file_id}/complete`);
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
