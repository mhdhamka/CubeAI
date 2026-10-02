// @vitest-environment jsdom

import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import Home from "../apps/web/app/page";

vi.mock("../packages/cube-renderer/CubePlayer", () => ({
  CubePlayer: () => <div aria-label="3D cube preview" />,
}));

afterEach(cleanup);

describe("Cube Lab dashboard", () => {
  it("shows the scanner view after choosing Scanner", () => {
    render(<Home />);

    expect(screen.getByRole("main")).toHaveClass("min-h-screen", "bg-paper");
    fireEvent.click(screen.getByRole("button", { name: "scanner" }));

    expect(
      screen.getByRole("heading", { name: "Bring a cube into the lab" }),
    ).toBeInTheDocument();
  });

  it("applies the selected color to a sticker", () => {
    render(<Home />);

    fireEvent.click(screen.getByRole("button", { name: "Set Yellow" }));
    fireEvent.click(
      screen.getByRole("button", { name: "U sticker 1: White" }),
    );

    expect(
      screen.getByRole("button", { name: "U sticker 1: Yellow" }),
    ).toHaveAttribute("aria-pressed", "true");
  });
});