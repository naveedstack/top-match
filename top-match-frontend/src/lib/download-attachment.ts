import { toAbsoluteApiUrl } from "@/lib/api";

export class AttachmentTokenExpiredError extends Error {
  constructor() {
    super("File link expired");
    this.name = "AttachmentTokenExpiredError";
  }
}

export async function downloadAttachment(url: string, filename: string): Promise<void> {
  const response = await fetch(toAbsoluteApiUrl(url));
  if (response.status === 401) {
    throw new AttachmentTokenExpiredError();
  }
  if (!response.ok) {
    throw new Error("Could not download file");
  }
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}
