"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { closeJob, createJob, exportJob, getJob, getLeaderboard, getPublicJob, listJobs, updateJob } from "@/api/jobs";
import { isNotFoundError } from "@/lib/api-error";
import { queryKeys } from "@/lib/query-keys";
import type { ExportRequest, LeaderboardQuery } from "@/types/applications";
import type { JobCreateRequest, JobUpdateRequest } from "@/types/jobs";

export function useJobs() {
  return useQuery({
    queryKey: queryKeys.jobs.all,
    queryFn: listJobs,
  });
}

export function useJob(jobId: string) {
  return useQuery({
    queryKey: queryKeys.jobs.detail(jobId),
    queryFn: () => getJob(jobId),
    enabled: Boolean(jobId),
    retry: (failureCount, error) => {
      if (isNotFoundError(error)) {
        return false;
      }
      return failureCount < 2;
    },
  });
}

export function usePublicJob(slug: string) {
  return useQuery({
    queryKey: queryKeys.jobs.public(slug),
    queryFn: () => getPublicJob(slug),
    enabled: Boolean(slug),
    retry: (failureCount, error) => {
      if (isNotFoundError(error)) {
        return false;
      }
      return failureCount < 2;
    },
  });
}

export function useLeaderboard(
  jobId: string,
  query: LeaderboardQuery = {},
  { enabled = true }: { enabled?: boolean } = {},
) {
  return useQuery({
    queryKey: queryKeys.jobs.leaderboard(jobId, query),
    queryFn: () => getLeaderboard(jobId, query),
    enabled: Boolean(jobId) && enabled,
    refetchInterval: (result) => (result.state.error ? false : 3_000),
    retry: (failureCount, error) => {
      if (isNotFoundError(error)) {
        return false;
      }
      return failureCount < 2;
    },
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: JobCreateRequest) => createJob(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.jobs.all });
    },
  });
}

export function useUpdateJob(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: JobUpdateRequest) => updateJob(jobId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.jobs.all });
      void queryClient.invalidateQueries({ queryKey: queryKeys.jobs.detail(jobId) });
    },
  });
}

export function useCloseJob(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => closeJob(jobId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.jobs.all });
      void queryClient.invalidateQueries({ queryKey: queryKeys.jobs.detail(jobId) });
    },
  });
}

export function useExportJob(jobId: string) {
  return useMutation({
    mutationFn: (body: ExportRequest) => exportJob(jobId, body),
  });
}
