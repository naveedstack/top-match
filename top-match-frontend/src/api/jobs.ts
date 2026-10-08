import { api } from "@/lib/api";
import type { ExportRequest, Leaderboard, LeaderboardQuery } from "@/types/applications";
import type { Job, JobCreateRequest, JobDetail, JobListItem, JobUpdateRequest, PublicJob } from "@/types/jobs";

export async function listJobs(): Promise<JobListItem[]> {
  const { data } = await api.get<JobListItem[]>("/jobs");
  return data;
}

export async function getJob(jobId: string): Promise<JobDetail> {
  const { data } = await api.get<JobDetail>(`/jobs/${jobId}`);
  return data;
}

export async function createJob(body: JobCreateRequest): Promise<Job> {
  const { data } = await api.post<Job>("/jobs", body);
  return data;
}

export async function updateJob(jobId: string, body: JobUpdateRequest): Promise<Job> {
  const { data } = await api.patch<Job>(`/jobs/${jobId}`, body);
  return data;
}

export async function closeJob(jobId: string): Promise<Job> {
  const { data } = await api.post<Job>(`/jobs/${jobId}/close`);
  return data;
}

export async function getPublicJob(slug: string): Promise<PublicJob> {
  const { data } = await api.get<PublicJob>(`/public/jobs/${slug}`);
  return data;
}

export async function getLeaderboard(
  jobId: string,
  query: LeaderboardQuery = {},
): Promise<Leaderboard> {
  const { data } = await api.get<Leaderboard>(`/jobs/${jobId}/leaderboard`, {
    params: query,
    // FastAPI reads repeated keys (status=a&status=b), not status[]=a.
    paramsSerializer: { indexes: null },
  });
  return data;
}

export async function exportJob(jobId: string, body: ExportRequest): Promise<string> {
  const { data } = await api.post<string>(`/jobs/${jobId}/exports`, body, {
    responseType: "text",
  });
  return data;
}
