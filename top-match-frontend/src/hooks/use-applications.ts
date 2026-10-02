"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { applyToJob, getApplication, rescoreApplication, uploadResume } from "@/api/applications";
import { isNotFoundError } from "@/lib/api-error";
import { queryKeys } from "@/lib/query-keys";
import type { ApplicationCreateRequest } from "@/types/applications";

export function useApplication(applicationId: string) {
  return useQuery({
    queryKey: queryKeys.applications.detail(applicationId),
    queryFn: () => getApplication(applicationId),
    enabled: Boolean(applicationId),
    refetchInterval: (result) => {
      if (result.state.error) {
        return false;
      }
      const status = result.state.data?.status;
      if (status === "received" || status === "processing") {
        return 3_000;
      }
      return false;
    },
    retry: (failureCount, error) => {
      if (isNotFoundError(error)) {
        return false;
      }
      return failureCount < 2;
    },
  });
}

export function useUploadResume() {
  return useMutation({
    mutationFn: (file: Blob) => uploadResume(file),
  });
}

export function useApply(slug: string) {
  return useMutation({
    mutationFn: (body: ApplicationCreateRequest) => applyToJob(slug, body),
  });
}

export function useRescoreApplication(jobId: string, applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => rescoreApplication(applicationId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.applications.detail(applicationId),
      });
      void queryClient.invalidateQueries({ queryKey: ["jobs", jobId, "leaderboard"] });
    },
  });
}
