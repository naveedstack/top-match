export type JobStatus = "open" | "closed";

export type ApplicationCounts = {
  received: number;
  processing: number;
  scored: number;
  refused: number;
  failed: number;
};

export type Job = {
  id: string;
  title: string;
  description: string;
  requirements: string;
  public_slug: string;
  public_url: string;
  status: JobStatus;
  created_at: string;
  closed_at: string | null;
};

export type JobListItem = Job & {
  application_counts: ApplicationCounts;
};

export type JobDetail = Job & {
  application_counts: ApplicationCounts;
  screening_disclaimer: string;
};

export type PublicJob = {
  title: string;
  description: string;
  requirements: string;
  status: JobStatus;
  privacy_notice: string;
  ai_screening_notice: string;
  screening_disclaimer: string;
};

export type JobCreateRequest = {
  title: string;
  description: string;
  requirements: string;
};

export type JobUpdateRequest = {
  title?: string;
  description?: string;
  requirements?: string;
};
