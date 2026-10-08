import type { GuardrailError } from "@/types/forms";

export type ApiValidationIssue = {
  loc: (string | number)[];
  msg: string;
  type: string;
};

export type ApiErrorBody = {
  detail?: string | ApiValidationIssue[];
  field_errors?: Record<string, string>;
  guardrail_errors?: GuardrailError[];
};
