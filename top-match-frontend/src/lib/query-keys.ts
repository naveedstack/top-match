import type { LeaderboardQuery } from "@/types/applications";

export const queryKeys = {
  auth: {
    me: ["auth", "me"] as const,
  },
  jobs: {
    all: ["jobs"] as const,
    detail: (jobId: string) => ["jobs", jobId] as const,
    public: (slug: string) => ["jobs", "public", slug] as const,
    leaderboard: (jobId: string, query: LeaderboardQuery) =>
      ["jobs", jobId, "leaderboard", query] as const,
  },
  applications: {
    detail: (applicationId: string) => ["applications", applicationId] as const,
  },
};
