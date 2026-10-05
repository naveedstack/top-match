import type { ApplicationCounts } from "@/types/jobs";
import type { ApplicationAnswer } from "@/types/forms";

export type ApplicationStatus = "received" | "processing" | "scored" | "refused" | "failed";

export type Citation = {
  claim: string;
  quote: string;
};

export type ResumeUploaded = {
  id: string;
};

export type ResumeUploadUrlRequest = {
  content_type: "application/pdf";
  byte_size: number;
};

export type AttachmentUploadUrlRequest = {
  field_id: string;
  filename: string;
  content_type: string;
  byte_size: number;
};

export type ResumeUploadUrlResponse = {
  file_id: string;
  upload_url: string;
  headers: Record<string, string>;
  expires_at: string;
};

export type ApplicationCreateRequest = {
  email: string;
  file_id: string;
  consented: true;
  answers?: Record<string, string | number | string[]>;
};

export type ApplicationAccepted = {
  id: string;
  status: ApplicationStatus;
};

export type LeaderboardItem = {
  id: string;
  email: string;
  status: ApplicationStatus;
  score: number | null;
  needs_review: boolean;
  created_at: string;
};

export type LeaderboardQuery = {
  status?: ApplicationStatus;
  limit?: number;
  offset?: number;
};

export type Leaderboard = {
  items: LeaderboardItem[];
  counts: ApplicationCounts;
  total: number;
  screening_disclaimer: string;
};

export type ApplicationDetail = {
  id: string;
  email: string;
  status: ApplicationStatus;
  score: number | null;
  created_at: string;
  is_resume: boolean | null;
  refusal_reason: string | null;
  key_strengths: string[];
  missing_requirements: string[];
  citations: Citation[];
  injection_suspected: boolean | null;
  needs_review: boolean | null;
  resume_url: string | null;
  answers: ApplicationAnswer[];
};

export type ExportRequest = {
  application_ids: string[];
  top_n?: never;
} | {
  top_n: number;
  application_ids?: never;
};
