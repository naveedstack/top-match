import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { useState } from "react";
import { afterEach, describe, expect, it } from "vitest";

import { ConditionBuilder } from "@/components/forms/condition-builder";
import { newConditionField, type ConditionField } from "@/lib/condition-presets";
import type { GuardrailError } from "@/types/forms";

// The conditions after the most recent change, as the parent form would hold them.
const saved: { current: ConditionField[] } = { current: [] };

afterEach(() => {
  cleanup();
  saved.current = [];
});

function Harness({
  initial = [],
  blocked = [],
}: {
  initial?: ConditionField[];
  blocked?: GuardrailError[];
}) {
  const [conditions, setConditions] = useState(initial);
  return (
    <ConditionBuilder
      blocked={blocked}
      conditions={conditions}
      disabled={false}
      onChange={(next) => {
        saved.current = next;
        setConditions(next);
      }}
      warnings={[]}
    />
  );
}

function card(title: string): HTMLElement {
  return screen.getByRole("article", { name: `${title} condition` });
}

describe("ConditionBuilder", () => {
  it("adds a preset in one click as a must condition", () => {
    render(<Harness />);

    fireEvent.click(screen.getByRole("button", { name: /Travel/ }));

    expect(saved.current).toHaveLength(1);
    expect(saved.current[0].condition.preset).toBe("travel");
    expect(saved.current[0].condition.importance).toBe("must");
    expect(within(card("Travel")).getByRole("radio", { name: "Must" })).toHaveProperty(
      "ariaChecked",
      "true",
    );
  });

  it("asks for the country before adding work authorization", () => {
    render(<Harness />);

    fireEvent.click(screen.getByRole("button", { name: /Work authorization/ }));
    expect(saved.current).toHaveLength(0);
    fireEvent.change(screen.getByPlaceholderText("e.g. Pakistan"), {
      target: { value: "Pakistan" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Add" }));

    expect(saved.current).toHaveLength(1);
    expect(saved.current[0].label).toBe("Can you legally work in Pakistan?");
  });

  it("switching importance moves between knockout, scoring and neither", () => {
    render(<Harness initial={[newConditionField("travel")]} />);
    const travel = card("Travel");

    fireEvent.click(within(travel).getByRole("radio", { name: "Preferred" }));
    expect(saved.current[0].knockout).toBeNull();
    expect(saved.current[0].scoring?.weight).toBe(1);
    expect(within(travel).getByText(/Weight/)).toBeTruthy();

    fireEvent.click(within(travel).getByRole("radio", { name: "Info only" }));
    expect(saved.current[0].knockout).toBeNull();
    expect(saved.current[0].scoring).toBeNull();
  });

  it("sets the minimum English level from the scale", () => {
    render(<Harness initial={[newConditionField("english_level")]} />);

    fireEvent.change(within(card("English level")).getByRole("combobox"), {
      target: { value: "Fluent" },
    });

    const field = saved.current[0];
    expect(field.type !== "number" && field.knockout?.allowed_values).toEqual(["Fluent"]);
  });

  it("shows guardrail errors with the suggested alternative on the condition", () => {
    const field = newConditionField("travel");
    render(
      <Harness
        blocked={[
          {
            target: field.id,
            category: "nationality",
            message: "This screens on nationality or citizenship, which is not allowed.",
            suggestion: "Ask about work authorization instead of nationality.",
          },
        ]}
        initial={[field]}
      />,
    );

    const alert = within(card("Travel")).getByRole("alert");
    expect(alert.textContent).toContain("Ask about work authorization instead of nationality.");
  });
});
