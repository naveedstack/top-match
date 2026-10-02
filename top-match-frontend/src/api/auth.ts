import { api } from "@/lib/api";
import type { AuthResponse, LoginRequest, Recruiter, RegisterRequest } from "@/types/auth";

export function toRecruiter(auth: AuthResponse): Recruiter {
  return {
    id: auth.id,
    company_name: auth.company_name,
    email: auth.email,
  };
}

export async function register(body: RegisterRequest): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>("/auth/register", body);
  return data;
}

export async function login(body: LoginRequest): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>("/auth/login", body);
  return data;
}

export async function logout(refreshToken: string): Promise<void> {
  await api.post("/auth/logout", { refresh_token: refreshToken });
}

export async function getMe(): Promise<Recruiter> {
  const { data } = await api.get<Recruiter>("/auth/me");
  return data;
}
