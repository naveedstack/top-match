export type FileAccept = "pdf" | "docx" | "png" | "jpeg";

export type FormFieldType = "text" | "number" | "dropdown" | "radio" | "checkboxes" | "file";

type FormFieldBase = {
  id: string;
  label: string;
  help_text?: string | null;
  required: boolean;
};

export type ChoiceKnockout = {
  reason: string;
  allowed_values: string[];
};

export type NumberKnockout = {
  reason: string;
  min?: number | null;
  max?: number | null;
};

export type ChoiceScoring = {
  weight: number;
  option_scores: Record<string, number>;
};

export type NumberScoring = {
  weight: number;
  target: number;
  // "at_most" gives full points at or below the target (expected salary).
  direction?: "at_least" | "at_most";
};

export type ConditionPreset =
  | "work_authorization"
  | "location"
  | "work_mode"
  | "working_hours"
  | "english_level"
  | "notice_period"
  | "expected_salary"
  | "credential"
  | "travel";

export type ConditionImportance = "must" | "preferred" | "info";

export type ConditionVerdict = "pass" | "partial" | "fail" | "not_scored";

export type SalaryRange = {
  currency: string;
  min: number;
  max: number;
};

export type JobCondition = {
  preset: ConditionPreset;
  importance: ConditionImportance;
  // Candidate-facing line shown under "Before you apply" for must conditions.
  summary: string;
  salary?: SalaryRange | null;
};

export type GuardrailError = {
  // A form field id, or "requirements".
  target: string;
  category: string;
  message: string;
  suggestion: string;
};

export type FormWarning = {
  field_id: string;
  message: string;
};

export type TextFormField = FormFieldBase & {
  type: "text";
  multiline: boolean;
  max_length: number;
};

export type NumberFormField = FormFieldBase & {
  type: "number";
  min?: number | null;
  max?: number | null;
  integer_only: boolean;
  knockout?: NumberKnockout | null;
  scoring?: NumberScoring | null;
  condition?: JobCondition | null;
};

export type ChoiceFormField = FormFieldBase & {
  type: "dropdown" | "radio" | "checkboxes";
  options: string[];
  // Only dropdown and radio fields can be knockouts.
  knockout?: ChoiceKnockout | null;
  scoring?: ChoiceScoring | null;
  // Only dropdown and radio fields can be job conditions.
  condition?: JobCondition | null;
};

export type FileFormField = FormFieldBase & {
  type: "file";
  accept: FileAccept[];
};

export type FormField = TextFormField | NumberFormField | ChoiceFormField | FileFormField;

export type FormAnswerValue = string | number | string[] | null;

export type ApplicationAnswer = {
  field_id: string;
  label: string;
  type: FormFieldType;
  value: FormAnswerValue;
  filename?: string | null;
  download_url?: string | null;
  condition?: JobCondition | null;
  condition_verdict?: ConditionVerdict | null;
};

export const FILE_ACCEPT_MIME: Record<FileAccept, string> = {
  pdf: "application/pdf",
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  png: "image/png",
  jpeg: "image/jpeg",
};

export const FILE_ACCEPT_LABEL: Record<FileAccept, string> = {
  pdf: "PDF",
  docx: "DOCX",
  png: "PNG",
  jpeg: "JPEG",
};

export const FORM_FIELD_TYPES: Array<{ type: FormFieldType; label: string; icon: string }> = [
  { type: "text", label: "Text", icon: "title" },
  { type: "number", label: "Number", icon: "pin" },
  { type: "dropdown", label: "Dropdown", icon: "arrow_drop_down_circle" },
  { type: "radio", label: "Single choice", icon: "radio_button_checked" },
  { type: "checkboxes", label: "Multiple choice", icon: "check_box" },
  { type: "file", label: "File upload", icon: "attach_file" },
];

export const MAX_WEIGHT = 10;

export const YES_NO_OPTIONS = ["Yes", "No"];

export function newYesNoKnockout(): ChoiceFormField {
  return {
    id: crypto.randomUUID(),
    type: "radio",
    label: "",
    help_text: "",
    required: true,
    options: [...YES_NO_OPTIONS],
    knockout: { reason: "", allowed_values: ["Yes"] },
  };
}

export const MAX_FORM_FIELDS = 20;
export const MAX_CONDITIONS = 10;
export const MAX_FILE_FIELDS = 5;
export const TEXT_MAX_LENGTH_DEFAULT = 500;
export const TEXT_MAX_LENGTH_CAP = 5000;

export function newFormField(type: FormFieldType): FormField {
  const id = crypto.randomUUID();
  const base = { id, label: "", help_text: "", required: true };
  if (type === "text") {
    return { ...base, type, multiline: false, max_length: TEXT_MAX_LENGTH_DEFAULT };
  }
  if (type === "number") {
    return { ...base, type, min: null, max: null, integer_only: false };
  }
  if (type === "file") {
    return { ...base, type, accept: ["pdf"] };
  }
  return { ...base, type, options: ["Option 1", "Option 2"] };
}
