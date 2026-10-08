import { describe, expect, it } from "vitest";

import {
  ENGLISH_LEVELS,
  PRESET_ORDER,
  beforeYouApply,
  isConditionField,
  newConditionField,
  passingAnswers,
  thresholdOf,
  validateCondition,
  withImportance,
  withPassing,
  withSalary,
  withThreshold,
  type ConditionField,
} from "@/lib/condition-presets";
import { validateFormFields } from "@/lib/form-validation";
import { MAX_CONDITIONS, MAX_FORM_FIELDS, newFormField, type ChoiceFormField } from "@/types/forms";

function choice(field: ConditionField): ChoiceFormField & ConditionField {
  if (field.type === "number") {
    throw new Error("expected a choice condition");
  }
  return field;
}

describe("newConditionField", () => {
  it.each(PRESET_ORDER)("creates a valid must condition for %s", (preset) => {
    const field = newConditionField(preset, "Pakistan");

    expect(isConditionField(field)).toBe(true);
    expect(field.condition.importance).toBe("must");
    expect(field.required).toBe(true);
    expect(field.knockout?.reason).toBeTruthy();
    expect(field.scoring ?? null).toBeNull();
    expect(validateCondition(field)).toBe("");
  });

  it("writes the place into the question, summary and options", () => {
    const field = choice(newConditionField("location", "Lahore"));

    expect(field.label).toBe("Are you based in Lahore or willing to relocate?");
    expect(field.condition.summary).toBe("Based in Lahore or willing to relocate");
    expect(passingAnswers(field)).toEqual(["Based in Lahore", "Willing to relocate to Lahore"]);
  });

  it("uses a fixed, ordered English scale", () => {
    const field = choice(newConditionField("english_level"));

    expect(field.type).toBe("dropdown");
    expect(field.options).toEqual(ENGLISH_LEVELS);
    expect(passingAnswers(field)).toEqual(["Professional", "Fluent"]);
  });
});

describe("importance", () => {
  it("must is a knockout, preferred is scored, info has neither", () => {
    const must = choice(newConditionField("travel"));
    const preferred = choice(withImportance(must, "preferred"));
    const info = withImportance(preferred, "info");

    expect(preferred.knockout).toBeNull();
    expect(preferred.scoring?.option_scores).toEqual({ Yes: 1, No: 0 });
    expect(info.knockout).toBeNull();
    expect(info.scoring).toBeNull();
    expect(info.condition.importance).toBe("info");
  });

  it("keeps the passing answers when moving between must and preferred", () => {
    const must = withPassing(newConditionField("work_mode"), ["Onsite", "Hybrid"]);
    const back = choice(withImportance(withImportance(must, "preferred"), "must"));

    expect(back.knockout?.allowed_values).toEqual(["Onsite", "Hybrid"]);
  });

  it("points salary knockout and scoring at the range maximum", () => {
    const must = withSalary(newConditionField("expected_salary"), {
      currency: "PKR",
      min: 150_000,
      max: 250_000,
    });
    const preferred = withImportance(must, "preferred");

    expect(must.type === "number" && must.knockout).toEqual({
      reason: "Expected salary above the range",
      max: 250_000,
    });
    expect(preferred.type === "number" && preferred.scoring).toEqual({
      weight: 1,
      target: 250_000,
      direction: "at_most",
    });
  });
});

describe("ordered scales", () => {
  it("a minimum English level passes that level and above", () => {
    const field = choice(withThreshold(newConditionField("english_level"), "Conversational"));

    expect(passingAnswers(field)).toEqual(["Conversational", "Professional", "Fluent"]);
    expect(thresholdOf(field)).toBe("Conversational");
  });

  it("a latest start passes that notice period and shorter", () => {
    const field = choice(withThreshold(newConditionField("notice_period"), "Within 2 weeks"));

    expect(passingAnswers(field)).toEqual(["Immediately", "Within 2 weeks"]);
    expect(thresholdOf(field)).toBe("Within 2 weeks");
  });
});

describe("validation", () => {
  it("rejects a bad salary range and currency", () => {
    const field = newConditionField("expected_salary");

    expect(validateCondition(withSalary(field, { currency: "PKR", min: 300, max: 200 }))).toMatch(
      /salary range/,
    );
    expect(validateCondition(withSalary(field, { currency: "rs", min: 1, max: 2 }))).toMatch(
      /currency/,
    );
  });

  it("requires a passing answer for must and preferred, but not info", () => {
    const empty = withPassing(newConditionField("travel"), []);

    expect(validateCondition(empty)).toMatch(/at least one answer/);
    expect(validateCondition(withImportance(empty, "info"))).toBe("");
  });

  it("counts questions and conditions against separate limits", () => {
    const questions = Array.from({ length: MAX_FORM_FIELDS }, () => ({
      ...newFormField("text"),
      label: "Question",
    }));
    const conditions = Array.from({ length: MAX_CONDITIONS }, () => newConditionField("travel"));

    expect(validateFormFields([...conditions, ...questions])).toBe("");
    expect(validateFormFields([...conditions, newConditionField("travel")])).toMatch(
      /job conditions/,
    );
    expect(validateFormFields([...questions, { ...newFormField("text"), label: "One more" }])).toMatch(
      /custom questions/,
    );
  });
});

describe("beforeYouApply", () => {
  it("lists must summaries only, in order", () => {
    const auth = newConditionField("work_authorization", "Pakistan");
    const travel = withImportance(newConditionField("travel"), "preferred");
    const english = newConditionField("english_level");

    expect(beforeYouApply([auth, travel, english, newFormField("text")])).toEqual([
      "Legally authorized to work in Pakistan",
      "Professional English or better",
    ]);
  });
});
