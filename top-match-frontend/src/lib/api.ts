import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "@/lib/token-storage";
import type { AuthResponse } from "@/types/auth";

const baseURL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1";

type RetriableConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
};

export const api = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
});

const refreshClient = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
});

let refreshPromise: Promise<string> | null = null;

function isAuthEndpoint(url: string | undefined): boolean {
  if (!url) {
    return false;
  }
  return ["/auth/login", "/auth/register", "/auth/refresh", "/auth/logout"].some((path) =>
    url.includes(path),
  );
}

async function refreshAccessToken(): Promise<string> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    throw new Error("Missing refresh token");
  }
  const { data } = await refreshClient.post<AuthResponse>("/auth/refresh", {
    refresh_token: refreshToken,
  });
  setTokens(data);
  return data.access_token;
}

function refreshOnce(): Promise<string> {
  refreshPromise ??= refreshAccessToken().finally(() => {
    refreshPromise = null;
  });
  return refreshPromise;
}

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined;
    const shouldRefresh =
      error.response?.status === 401 &&
      original !== undefined &&
      !original._retry &&
      !isAuthEndpoint(original.url);

    if (!shouldRefresh || original === undefined) {
      return Promise.reject(error);
    }

    original._retry = true;
    try {
      const accessToken = await refreshOnce();
      original.headers.set("Authorization", `Bearer ${accessToken}`);
      return await api(original);
    } catch (refreshError) {
      clearTokens();
      return Promise.reject(refreshError);
    }
  },
);

export function toAbsoluteApiUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  const origin = new URL(baseURL).origin;
  return `${origin}${path.startsWith("/") ? path : `/${path}`}`;
}
