import type { ApplicationCounts } from "@/types/jobs";
import type { ApplicationAnswer } from "@/types/forms";

export type ApplicationStatus =
  | "received"
  | "processing"
  | "scored"
  | "refused"
  | "failed"
  | "knocked_out";

export const STATUS_LABEL: Record<ApplicationStatus, string> = {
  received: "Received",
  processing: "Processing",
  scored: "Scored",
  refused: "Refused",
  failed: "Failed",
  knocked_out: "Knocked out",
};

export type ScreeningPhase = "accept" | "knockout" | "answers" | "resume";

export type PhaseOutcome = "pass" | "fail" | "review" | "error" | "skipped";

export const SCREENING_PHASES: ScreeningPhase[] = ["accept", "knockout", "answers", "resume"];

export const PHASE_LABEL: Record<ScreeningPhase, string> = {
  accept: "Accept",
  knockout: "Knockout",
  answers: "Answers",
  resume: "Resume",
};

export type StageInfo = {
  current_phase: ScreeningPhase | null;
  stopped_phase: ScreeningPhase | null;
  stop_code: string | null;
  stop_reason: string | null;
  reviewed_at: string | null;
};

export function stageLabel(stage: StageInfo): string {
  if (stage.stopped_phase) {
    return `Stopped at ${PHASE_LABEL[stage.stopped_phase]}`;
  }
  return stage.current_phase ? PHASE_LABEL[stage.current_phase] : "Not started";
}

export type PhaseResultItem = {
  phase: ScreeningPhase;
  outcome: PhaseOutcome;
  reasons: Array<{ code: string; message: string; field_id?: string }>;
  overridden: boolean;
  created_at: string;
};

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

export type LeaderboardItem = StageInfo & {
  id: string;
  email: string;
  status: ApplicationStatus;
  score: number | null;
  needs_review: boolean;
  created_at: string;
};

export type LeaderboardQuery = {
  status?: ApplicationStatus | ApplicationStatus[];
  stage?: ScreeningPhase;
  limit?: number;
  offset?: number;
};

export type Leaderboard = {
  items: LeaderboardItem[];
  counts: ApplicationCounts;
  total: number;
  screening_disclaimer: string;
};

export type ApplicationDetail = StageInfo & {
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
  answers_score: number | null;
  phase_results: PhaseResultItem[];
};

export type ExportRequest = {
  application_ids: string[];
  top_n?: never;
} | {
  top_n: number;
  application_ids?: never;
};
