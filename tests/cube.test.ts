import { describe, expect, test } from "vitest";
import { Cube } from "../packages/cube-core/Cube";
import { Move } from "../packages/cube-core/Move";

describe("Cube", () => {
  test("new cube should be solved", () => {
    const cube = new Cube();

    expect(cube.isSolved()).toBe(true);
  });

  test.each([
    "U",
    "D",
    "R",
    "L",
    "F",
    "B",
  ] as Move[])("%s four times should solve the cube", (move) => {
    const cube = new Cube();

    cube.move(move);
    cube.move(move);
    cube.move(move);
    cube.move(move);

    expect(cube.isSolved()).toBe(true);
  });

  test.each([
    ["U", "U'"],
    ["D", "D'"],
    ["R", "R'"],
    ["L", "L'"],
    ["F", "F'"],
    ["B", "B'"],
  ] as [Move, Move][])(
    "%s followed by %s should solve the cube",
    (move, inverse) => {
      const cube = new Cube();

      cube.move(move);
      cube.move(inverse);

      expect(cube.isSolved()).toBe(true);
    }
  );

  test.each([
    "U2",
    "D2",
    "R2",
    "L2",
    "F2",
    "B2",
  ] as Move[])("%s twice should solve the cube", (move) => {
    const cube = new Cube();

    cube.move(move);
    cube.move(move);

    expect(cube.isSolved()).toBe(true);
  });

  test("R followed by R' returns to solved", () => {
    const cube = new Cube();

    cube.move("R");
    cube.move("R'");

    expect(cube.isSolved()).toBe(true);
  });

  test("U followed by U' returns to solved", () => {
    const cube = new Cube();

    cube.move("U");
    cube.move("U'");

    expect(cube.isSolved()).toBe(true);
  });

  test("F followed by F' returns to solved", () => {
    const cube = new Cube();

    cube.move("F");
    cube.move("F'");

    expect(cube.isSolved()).toBe(true);
  });

  test("R U followed by U' R' returns to solved", () => {
    const cube = new Cube();

    cube.applyMoves(["R", "U"]);
    cube.applyMoves(["U'", "R'"]);

    expect(cube.isSolved()).toBe(true);
  });
});