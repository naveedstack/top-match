import type { FormField, FormWarning } from "@/types/forms";

export type JobStatus = "open" | "closed";

export type ApplicationCounts = {
  received: number;
  processing: number;
  scored: number;
  refused: number;
  failed: number;
  knocked_out: number;
};

export const EMPTY_COUNTS: ApplicationCounts = {
  received: 0,
  processing: 0,
  scored: 0,
  refused: 0,
  failed: 0,
  knocked_out: 0,
};

export function totalApplications(counts: ApplicationCounts): number {
  return Object.values(counts).reduce((sum, value) => sum + value, 0);
}

export type Job = {
  id: string;
  title: string;
  description: string;
  requirements: string;
  form_fields: FormField[];
  company_slug: string;
  public_slug: string;
  public_url: string;
  status: JobStatus;
  created_at: string;
  closed_at: string | null;
  form_warnings: FormWarning[];
};

export type JobListItem = Job & {
  application_counts: ApplicationCounts;
};

export type JobDetail = Job & {
  application_counts: ApplicationCounts;
  screening_disclaimer: string;
  form_locked: boolean;
};

export type PublicJob = {
  title: string;
  description: string;
  requirements: string;
  form_fields: FormField[];
  company_slug: string;
  status: JobStatus;
  privacy_notice: string;
  ai_screening_notice: string;
  screening_disclaimer: string;
};

export type JobCreateRequest = {
  title: string;
  description: string;
  requirements: string;
  form_fields?: FormField[];
};

export type JobUpdateRequest = {
  title?: string;
  description?: string;
  requirements?: string;
  form_fields?: FormField[];
};
