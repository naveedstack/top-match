export type FileAccept = "pdf" | "docx" | "png" | "jpeg";

export type FormFieldType = "text" | "number" | "dropdown" | "radio" | "checkboxes" | "file";

type FormFieldBase = {
  id: string;
  label: string;
  help_text?: string | null;
  required: boolean;
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
};

export type ChoiceFormField = FormFieldBase & {
  type: "dropdown" | "radio" | "checkboxes";
  options: string[];
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

export const MAX_FORM_FIELDS = 20;
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
