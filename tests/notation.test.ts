import { describe, expect, test } from "vitest";

import { parseAlgorithm } from "../packages/cube-notation/parser";
import { formatAlgorithm } from "../packages/cube-notation/formatter";
import { validateAlgorithm } from "../packages/cube-notation/validator";

describe("Cube notation", () => {
  test("parses an algorithm", () => {
    expect(
      parseAlgorithm("R U R' U2 F'")
    ).toEqual([
      "R",
      "U",
      "R'",
      "U2",
      "F'",
    ]);
  });

  test("formats moves", () => {
    expect(
      formatAlgorithm(["R", "U", "R'", "U2"])
    ).toBe("R U R' U2");
  });

  test("validates correct notation", () => {
    expect(
      validateAlgorithm("R U R' U2")
    ).toEqual({
      valid: true,
      invalidMoves: [],
    });
  });

  test("detects invalid notation", () => {
    expect(
      validateAlgorithm("R X HELLO")
    ).toEqual({
      valid: false,
      invalidMoves: ["X", "HELLO"],
    });
  });
});