import type {
  ChoiceFormField,
  ConditionImportance,
  ConditionPreset,
  FormField,
  JobCondition,
  NumberFormField,
  SalaryRange,
} from "@/types/forms";

export type ConditionField = (NumberFormField | ChoiceFormField) & { condition: JobCondition };

type ScaleDirection = "at_least" | "at_most";

export const ENGLISH_LEVELS = ["Basic", "Conversational", "Professional", "Fluent"];
export const NOTICE_PERIODS = [
  "Immediately",
  "Within 2 weeks",
  "Within 1 month",
  "Within 2 months",
  "More than 2 months",
];

// Presets whose options are a fixed, ordered scale, and which end of it passes.
export const ORDERED_SCALES: Partial<
  Record<ConditionPreset, { levels: string[]; direction: ScaleDirection; label: string }>
> = {
  english_level: { levels: ENGLISH_LEVELS, direction: "at_least", label: "Minimum level" },
  notice_period: { levels: NOTICE_PERIODS, direction: "at_most", label: "Latest start" },
};

export const IMPORTANCE_LABEL: Record<ConditionImportance, string> = {
  must: "Must",
  preferred: "Preferred",
  info: "Info only",
};

export const IMPORTANCE_HINT: Record<ConditionImportance, string> = {
  must: "Knockout. Failing stops the application before resume scoring.",
  preferred: "Adds to the answers score.",
  info: "Shown to you only. No effect on the score.",
};

const YES_NO = ["Yes", "No"];
const DEFAULT_SALARY: SalaryRange = { currency: "PKR", min: 100_000, max: 200_000 };

type PresetTemplate = {
  label: string;
  summary: string;
  reason: string;
  options: string[];
  passing: string[];
};

type PresetDefinition = {
  title: string;
  icon: string;
  // Asked once when the preset is added; written into the question text.
  place?: "Country" | "City";
  template: (place: string) => PresetTemplate;
};

function yesNo(label: string, summary: string, reason: string): PresetTemplate {
  return { label, summary, reason, options: YES_NO, passing: ["Yes"] };
}

function levelsFrom(levels: string[], threshold: string, direction: ScaleDirection): string[] {
  const index = levels.indexOf(threshold);
  return direction === "at_least" ? levels.slice(index) : levels.slice(0, index + 1);
}

export const CONDITION_PRESETS: Record<ConditionPreset, PresetDefinition> = {
  work_authorization: {
    title: "Work authorization",
    icon: "badge",
    place: "Country",
    template: (country) =>
      yesNo(
        `Can you legally work in ${country}?`,
        `Legally authorized to work in ${country}`,
        `Not authorized to work in ${country}`,
      ),
  },
  location: {
    title: "Location",
    icon: "location_on",
    place: "City",
    template: (city) => ({
      label: `Are you based in ${city} or willing to relocate?`,
      summary: `Based in ${city} or willing to relocate`,
      reason: `Not based in or relocating to ${city}`,
      options: [`Based in ${city}`, `Willing to relocate to ${city}`, "Neither"],
      passing: [`Based in ${city}`, `Willing to relocate to ${city}`],
    }),
  },
  work_mode: {
    title: "Work mode",
    icon: "apartment",
    template: () => ({
      label: "Which work arrangement can you commit to?",
      summary: "Able to work onsite",
      reason: "Cannot work onsite",
      options: ["Onsite", "Hybrid", "Remote"],
      passing: ["Onsite"],
    }),
  },
  working_hours: {
    title: "Working hours",
    icon: "schedule",
    template: () =>
      yesNo(
        "Can you work USA/UK shift hours?",
        "Available for USA/UK shift hours",
        "Not available for USA/UK shift hours",
      ),
  },
  english_level: {
    title: "English level",
    icon: "translate",
    template: () => ({
      label: "What is your English level?",
      summary: "Professional English or better",
      reason: "English level below Professional",
      options: ENGLISH_LEVELS,
      passing: levelsFrom(ENGLISH_LEVELS, "Professional", "at_least"),
    }),
  },
  notice_period: {
    title: "Notice period",
    icon: "event_available",
    template: () => ({
      label: "When could you start?",
      summary: "Able to start within 1 month",
      reason: "Cannot start within 1 month",
      options: NOTICE_PERIODS,
      passing: levelsFrom(NOTICE_PERIODS, "Within 1 month", "at_most"),
    }),
  },
  expected_salary: {
    title: "Expected salary",
    icon: "payments",
    template: () => ({
      label: "What is your expected monthly salary?",
      summary: "Expected salary within the role's range",
      reason: "Expected salary above the range",
      options: [],
      passing: [],
    }),
  },
  credential: {
    title: "Degree, license or certification",
    icon: "workspace_premium",
    template: () =>
      yesNo(
        "Do you hold the required degree, license or certification?",
        "Holds the required degree, license or certification",
        "Missing the required degree, license or certification",
      ),
  },
  travel: {
    title: "Travel",
    icon: "flight",
    template: () =>
      yesNo(
        "Are you able to travel for this role?",
        "Able to travel for work",
        "Unable to travel for work",
      ),
  },
};

export const PRESET_ORDER = Object.keys(CONDITION_PRESETS) as ConditionPreset[];

export function isConditionField(field: FormField): field is ConditionField {
  return (
    (field.type === "number" || field.type === "dropdown" || field.type === "radio") &&
    field.condition != null
  );
}

/** A new must condition from a preset. `place` fills the country or city, when the preset has one. */
export function newConditionField(preset: ConditionPreset, place = ""): ConditionField {
  const template = CONDITION_PRESETS[preset].template(place.trim());
  const base = { id: crypto.randomUUID(), label: template.label, help_text: "", required: true };
  const condition: JobCondition = { preset, importance: "must", summary: template.summary };
  if (preset === "expected_salary") {
    return {
      ...base,
      type: "number",
      min: 0,
      max: null,
      integer_only: true,
      condition: { ...condition, salary: DEFAULT_SALARY },
      knockout: { reason: template.reason, max: DEFAULT_SALARY.max },
    };
  }
  return {
    ...base,
    type: preset in ORDERED_SCALES ? "dropdown" : "radio",
    options: [...template.options],
    condition,
    knockout: { reason: template.reason, allowed_values: [...template.passing] },
  };
}

/** Answers that meet a choice condition, read from its knockout or scoring. */
export function passingAnswers(field: ChoiceFormField): string[] {
  if (field.knockout) {
    return field.knockout.allowed_values;
  }
  if (field.scoring) {
    return field.options.filter((option) => (field.scoring?.option_scores[option] ?? 0) >= 1);
  }
  return [];
}

function defaultPassing(field: ChoiceFormField): string[] {
  const scale = field.condition ? ORDERED_SCALES[field.condition.preset] : undefined;
  if (scale) {
    const middle = scale.levels[Math.floor(scale.levels.length / 2)];
    return levelsFrom(scale.levels, middle, scale.direction);
  }
  return field.options.slice(0, 1);
}

function choiceRules(
  field: ChoiceFormField,
  importance: ConditionImportance,
  passing: string[],
  reason: string,
  weight: number,
): Pick<ChoiceFormField, "knockout" | "scoring"> {
  if (importance === "must") {
    return { knockout: { reason, allowed_values: passing }, scoring: null };
  }
  if (importance === "preferred") {
    const optionScores = Object.fromEntries(field.options.map((option) => [option, passing.includes(option) ? 1 : 0]));
    return { knockout: null, scoring: { weight, option_scores: optionScores } };
  }
  return { knockout: null, scoring: null };
}

function numberRules(
  importance: ConditionImportance,
  salary: SalaryRange,
  reason: string,
  weight: number,
): Pick<NumberFormField, "knockout" | "scoring"> {
  if (importance === "must") {
    return { knockout: { reason, max: salary.max }, scoring: null };
  }
  if (importance === "preferred") {
    return { knockout: null, scoring: { weight, target: salary.max, direction: "at_most" } };
  }
  return { knockout: null, scoring: null };
}

function rebuild(
  field: ConditionField,
  importance: ConditionImportance,
  passing: string[] | null,
  salary: SalaryRange | null,
): ConditionField {
  const reason = field.knockout?.reason || `Does not meet: ${field.condition.summary}`;
  const weight = field.scoring?.weight ?? 1;
  const condition = { ...field.condition, importance };
  if (field.type === "number") {
    const range = salary ?? field.condition.salary ?? DEFAULT_SALARY;
    return {
      ...field,
      required: true,
      condition: { ...condition, salary: range },
      ...numberRules(importance, range, reason, weight),
    };
  }
  const current = passingAnswers(field);
  const answers = passing ?? (current.length > 0 ? current : defaultPassing(field));
  return {
    ...field,
    required: true,
    condition,
    ...choiceRules(field, importance, answers, reason, weight),
  };
}

/** Switch importance: must is a knockout, preferred is scored, info has neither. */
export function withImportance(field: ConditionField, importance: ConditionImportance): ConditionField {
  return rebuild(field, importance, null, null);
}

/** Set which answers meet a choice condition, keeping its importance. */
export function withPassing(field: ConditionField, passing: string[]): ConditionField {
  return rebuild(field, field.condition.importance, passing, null);
}

/** Set the salary range; the knockout and scoring follow its maximum. */
export function withSalary(field: ConditionField, salary: SalaryRange): ConditionField {
  return rebuild(field, field.condition.importance, null, salary);
}

export function withReason(field: ConditionField, reason: string): ConditionField {
  if (field.type === "number") {
    return field.knockout ? { ...field, knockout: { ...field.knockout, reason } } : field;
  }
  return field.knockout ? { ...field, knockout: { ...field.knockout, reason } } : field;
}

export function withWeight(field: ConditionField, weight: number): ConditionField {
  if (field.type === "number") {
    return field.scoring ? { ...field, scoring: { ...field.scoring, weight } } : field;
  }
  return field.scoring ? { ...field, scoring: { ...field.scoring, weight } } : field;
}

/** Set the minimum (or latest) passing level of an ordered scale. */
export function withThreshold(field: ConditionField, threshold: string): ConditionField {
  const scale = ORDERED_SCALES[field.condition.preset];
  if (!scale) {
    return field;
  }
  return withPassing(field, levelsFrom(scale.levels, threshold, scale.direction));
}

/** The level a scale condition passes from (at_least) or up to (at_most). */
export function thresholdOf(field: ChoiceFormField): string {
  const scale = field.condition ? ORDERED_SCALES[field.condition.preset] : undefined;
  if (!scale) {
    return "";
  }
  const passing = passingAnswers(field);
  const source = passing.length > 0 ? passing : defaultPassing(field);
  const indexes = source.map((item) => scale.levels.indexOf(item)).filter((index) => index >= 0);
  const index = scale.direction === "at_least" ? Math.min(...indexes) : Math.max(...indexes);
  return scale.levels[index] ?? "";
}

/** Candidate-facing summaries of the must conditions, in form order. */
export function beforeYouApply(fields: FormField[]): string[] {
  return fields
    .filter(isConditionField)
    .filter((field) => field.condition.importance === "must")
    .map((field) => field.condition.summary);
}

export function validateCondition(field: ConditionField): string {
  const name = field.label || CONDITION_PRESETS[field.condition.preset].title;
  if (!field.condition.summary.trim()) {
    return `${name} needs a summary for candidates`;
  }
  const salary = field.condition.salary;
  if (field.type === "number" && salary) {
    if (!/^[A-Z]{3}$/.test(salary.currency)) {
      return `${name} needs a three-letter currency code, such as PKR`;
    }
    if (!(salary.max > 0) || salary.min < 0 || salary.min > salary.max) {
      return `${name} needs a salary range with min at or below max`;
    }
  }
  if (field.type !== "number" && field.condition.importance !== "info" && passingAnswers(field).length === 0) {
    return `${name} needs at least one answer that meets it`;
  }
  return "";
}
