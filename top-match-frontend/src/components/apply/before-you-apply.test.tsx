import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { BeforeYouApply } from "@/components/apply/before-you-apply";

afterEach(cleanup);

describe("BeforeYouApply", () => {
  it("lists each must condition", () => {
    render(
      <BeforeYouApply
        items={["Legally authorized to work in Pakistan", "Professional English or better"]}
      />,
    );

    expect(screen.getByRole("heading", { name: "Before you apply" })).toBeTruthy();
    expect(screen.getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      "Legally authorized to work in Pakistan",
      "Professional English or better",
    ]);
  });

  it("renders nothing when the job has no must conditions", () => {
    const { container } = render(<BeforeYouApply items={[]} />);

    expect(container.innerHTML).toBe("");
  });
});
