export type Recruiter = {
  id: string;
  company_name: string;
  email: string;
};

export type AuthTokens = {
  access_token: string;
  refresh_token: string;
};

export type AuthResponse = Recruiter & AuthTokens;

export type RegisterRequest = {
  company_name: string;
  email: string;
  password: string;
};

export type LoginRequest = {
  email: string;
  password: string;
};

export type RefreshRequest = {
  refresh_token: string;
};
