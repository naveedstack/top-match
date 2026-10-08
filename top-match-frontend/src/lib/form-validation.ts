import { isConditionField, validateCondition } from "@/lib/condition-presets";
import {
  FILE_ACCEPT_MIME,
  MAX_CONDITIONS,
  MAX_FILE_FIELDS,
  MAX_FORM_FIELDS,
  TEXT_MAX_LENGTH_CAP,
  type FileAccept,
  type FormField,
} from "@/types/forms";

export type FormAnswers = Record<string, string | number | string[] | File | null | undefined>;

export function mimeForFile(file: File): string {
  if (file.type) {
    return file.type.split(";")[0].trim().toLowerCase();
  }
  const ext = file.name.split(".").pop()?.toLowerCase();
  if (ext === "pdf") {
    return FILE_ACCEPT_MIME.pdf;
  }
  if (ext === "docx") {
    return FILE_ACCEPT_MIME.docx;
  }
  if (ext === "png") {
    return FILE_ACCEPT_MIME.png;
  }
  if (ext === "jpg" || ext === "jpeg") {
    return FILE_ACCEPT_MIME.jpeg;
  }
  return "";
}

export function acceptForField(field: Extract<FormField, { type: "file" }>): string {
  const parts: string[] = [];
  for (const item of field.accept) {
    parts.push(FILE_ACCEPT_MIME[item]);
    if (item === "jpeg") {
      parts.push(".jpg", ".jpeg");
    } else {
      parts.push(`.${item}`);
    }
  }
  return parts.join(",");
}

export function validateFormFields(fields: FormField[]): string {
  const conditionCount = fields.filter(isConditionField).length;
  if (fields.length - conditionCount > MAX_FORM_FIELDS) {
    return `A form can have at most ${MAX_FORM_FIELDS} custom questions`;
  }
  if (conditionCount > MAX_CONDITIONS) {
    return `A form can have at most ${MAX_CONDITIONS} job conditions`;
  }
  const fileCount = fields.filter((field) => field.type === "file").length;
  if (fileCount > MAX_FILE_FIELDS) {
    return `A form can have at most ${MAX_FILE_FIELDS} file fields`;
  }
  const ids = new Set<string>();
  for (const field of fields) {
    if (ids.has(field.id)) {
      return "Field ids must be unique";
    }
    ids.add(field.id);
    if (!field.label.trim()) {
      return "Every field needs a label";
    }
    if (field.type === "text") {
      if (field.max_length < 1 || field.max_length > TEXT_MAX_LENGTH_CAP) {
        return `Text max length must be between 1 and ${TEXT_MAX_LENGTH_CAP}`;
      }
    }
    if (field.type === "number" && field.min != null && field.max != null && field.min > field.max) {
      return "Number min must be less than or equal to max";
    }
    if (field.type === "dropdown" || field.type === "radio" || field.type === "checkboxes") {
      const options = field.options.map((item) => item.trim()).filter(Boolean);
      if (options.length < 2) {
        return `${field.label || "A choice field"} needs at least two options`;
      }
      if (new Set(options).size !== options.length) {
        return "Options must be unique";
      }
    }
    if (field.type === "file" && field.accept.length === 0) {
      return "A file field needs at least one allowed type";
    }
    const knockoutMessage = validateKnockout(field);
    if (knockoutMessage) {
      return knockoutMessage;
    }
    const conditionMessage = isConditionField(field) ? validateCondition(field) : "";
    if (conditionMessage) {
      return conditionMessage;
    }
  }
  return "";
}

function validateKnockout(field: FormField): string {
  const name = field.label || "A knockout question";
  if ((field.type === "number" || field.type === "dropdown" || field.type === "radio") && field.knockout) {
    if (!field.required) {
      return `${name} is a knockout, so it must be required`;
    }
    if (!field.knockout.reason.trim()) {
      return `${name} needs a reason to show when someone fails it`;
    }
    if (field.type !== "number" && field.knockout.allowed_values.length === 0) {
      return `${name} needs at least one passing answer`;
    }
  }
  if (field.type === "number" && field.scoring && !(field.scoring.target > 0)) {
    return `${field.label || "A number question"} needs a target above zero`;
  }
  return "";
}

export function validateAnswers(
  fields: FormField[],
  answers: FormAnswers,
): Record<string, string> {
  const errors: Record<string, string> = {};
  for (const field of fields) {
    const value = answers[field.id];
    const missing = isMissing(field, value);
    if (field.required && missing) {
      errors[field.id] = "This field is required";
      continue;
    }
    if (missing) {
      continue;
    }
    if (field.type === "text" && typeof value === "string" && value.trim().length > field.max_length) {
      errors[field.id] = `Must be at most ${field.max_length} characters`;
    }
    if (field.type === "number") {
      const number = typeof value === "number" ? value : Number(value);
      if (!Number.isFinite(number)) {
        errors[field.id] = "Must be a number";
      } else if (field.integer_only && !Number.isInteger(number)) {
        errors[field.id] = "Must be a whole number";
      } else if (field.min != null && number < field.min) {
        errors[field.id] = `Must be at least ${field.min}`;
      } else if (field.max != null && number > field.max) {
        errors[field.id] = `Must be at most ${field.max}`;
      }
    }
    if (
      (field.type === "dropdown" || field.type === "radio") &&
      (typeof value !== "string" || !field.options.includes(value))
    ) {
      errors[field.id] = "Select a valid option";
    }
    if (field.type === "checkboxes") {
      if (!Array.isArray(value) || value.some((item) => !field.options.includes(item))) {
        errors[field.id] = "Select valid options";
      }
    }
    if (field.type === "file" && value instanceof File) {
      const mime = mimeForFile(value);
      const allowed = new Set(field.accept.map((item) => FILE_ACCEPT_MIME[item as FileAccept]));
      if (!allowed.has(mime)) {
        errors[field.id] = "File type is not allowed for this field";
      }
      if (value.size > 5 * 1024 * 1024) {
        errors[field.id] = "File must be at most 5 MB";
      }
    }
  }
  return errors;
}

function isMissing(field: FormField, value: FormAnswers[string]): boolean {
  if (value == null || value === "") {
    return true;
  }
  if (field.type === "text") {
    return typeof value !== "string" || !value.trim();
  }
  if (field.type === "checkboxes") {
    return !Array.isArray(value) || value.length === 0;
  }
  if (field.type === "file") {
    return !(value instanceof File);
  }
  return false;
}
