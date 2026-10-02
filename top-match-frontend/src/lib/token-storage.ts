import { emitSessionChanged } from "@/lib/auth-session";

const ACCESS_TOKEN_KEY = "topmatch.access_token";
const REFRESH_TOKEN_KEY = "topmatch.refresh_token";

function read(key: string): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(key);
}

export function getAccessToken(): string | null {
  return read(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return read(REFRESH_TOKEN_KEY);
}

export function hasStoredSession(): boolean {
  return Boolean(getAccessToken() || getRefreshToken());
}

export function setTokens(tokens: { access_token: string; refresh_token: string }): void {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  emitSessionChanged();
}

export function clearTokens(): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  emitSessionChanged();
}
