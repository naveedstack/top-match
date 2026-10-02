import { toAbsoluteApiUrl } from "@/lib/api";

export class ResumeTokenExpiredError extends Error {
  constructor() {
    super("Resume link expired");
    this.name = "ResumeTokenExpiredError";
  }
}

export async function fetchResumePdf(resumeUrl: string): Promise<Blob> {
  const response = await fetch(toAbsoluteApiUrl(resumeUrl));
  if (response.status === 401) {
    throw new ResumeTokenExpiredError();
  }
  if (!response.ok) {
    throw new Error("Could not load resume");
  }
  return response.blob();
}
