import axios from "axios";

import type { ApiErrorBody } from "@/types/api";

export function getApiErrorMessage(error: unknown, fallback = "Something went wrong"): string {
  if (axios.isAxiosError<ApiErrorBody>(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail) {
      return detail;
    }
    if (Array.isArray(detail)) {
      const messages = detail.map((issue) => issue.msg).filter(Boolean);
      if (messages.length > 0) {
        return messages.join(", ");
      }
    }
    return fallback;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export function getApiFieldErrors(error: unknown): Record<string, string> {
  if (axios.isAxiosError<ApiErrorBody>(error)) {
    const fieldErrors = error.response?.data?.field_errors;
    if (fieldErrors && typeof fieldErrors === "object") {
      return fieldErrors;
    }
  }
  return {};
}

export function isNotFoundError(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 404;
}
