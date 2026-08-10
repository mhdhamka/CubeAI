import { describe, expect, test } from "vitest";

import { Cube } from "../packages/cube-core/Cube";
import { SearchSolver } from "../packages/cube-solver/SearchSolver";
import { CubieCube } from "../packages/cube-solver/representation/CubieCube";
import { heuristic } from "../packages/cube-solver/heuristic/heuristic";

import {
  applyCubieMove,
} from "../packages/cube-solver/tables/moveTables";

describe("SearchSolver", () => {

  test("solved cube requires zero moves", () => {
    const cube = new Cube();
    const solver = new SearchSolver();

    const result = solver.solve(
      cube.getState()
    );

    expect(result.solved).toBe(true);
    expect(result.moves).toEqual([]);
    expect(result.moveCount).toBe(0);
  });

  describe("Heuristic", () => {

    test("solved cube has heuristic 0", () => {
      const cube = new CubieCube();

      expect(
        heuristic(cube)
      ).toBe(0);
    });

    test("scrambled cube has positive heuristic", () => {
      const cube = new CubieCube();

      const scrambled =
        applyCubieMove(cube, "R");

      expect(
        heuristic(scrambled)
      ).toBeGreaterThan(0);
    });

  });

  test("solves a one-move scramble", () => {
    const cube = new Cube();

    cube.move("R");

    const solver = new SearchSolver();
    const result = solver.solve(
      cube.getState()
    );

    expect(result.solved).toBe(true);

    cube.applyMoves(result.moves);

    expect(
      cube.isSolved()
    ).toBe(true);
  });

  test("solves a two-move scramble", () => {
    const cube = new Cube();

    cube.applyMoves([
      "R",
      "U",
    ]);

    const solver = new SearchSolver();
    const result = solver.solve(
      cube.getState()
    );

    expect(result.solved).toBe(true);

    cube.applyMoves(result.moves);

    expect(
      cube.isSolved()
    ).toBe(true);
  });

  test("solves a three-move scramble", () => {
    const cube = new Cube();

    cube.applyMoves([
      "R",
      "U",
      "F",
    ]);

    const solver = new SearchSolver();
    const result = solver.solve(
      cube.getState()
    );

    expect(result.solved).toBe(true);

    cube.applyMoves(result.moves);

    expect(
      cube.isSolved()
    ).toBe(true);
  });

  test("solution actually solves the cube", () => {
    const cube = new Cube();

    cube.move("R");
    cube.move("U");

    const solver = new SearchSolver();
    const result = solver.solve(
      cube.getState()
    );

    cube.applyMoves(result.moves);

    expect(
      cube.isSolved()
    ).toBe(true);
  });

  test("converts solved CubeState to solved CubieCube", () => {
    const cube = new Cube();

    const cubie =
      CubieCube.fromCubeState(
        cube.getState()
      );

    expect(
      cubie.isSolved()
    ).toBe(true);
  });

  test("compares CubeState conversion with R cubie move", () => {
    const cube = new Cube();

    cube.move("R");

    const converted =
      CubieCube.fromCubeState(
        cube.getState()
      );

    const solved = new CubieCube();

    const expected =
      applyCubieMove(
        solved,
        "R"
      );

    console.log("\n===== CubeState -> CubieCube =====");
    console.log("CP:", converted.cp);
    console.log("CO:", converted.co);
    console.log("EP:", converted.ep);
    console.log("EO:", converted.eo);

    console.log("\n===== applyCubieMove(solved, R) =====");
    console.log("CP:", expected.cp);
    console.log("CO:", expected.co);
    console.log("EP:", expected.ep);
    console.log("EO:", expected.eo);

    expect(converted.cp).toEqual(expected.cp);
    expect(converted.co).toEqual(expected.co);
    expect(converted.ep).toEqual(expected.ep);
    expect(converted.eo).toEqual(expected.eo);
  });

  test("CubeState conversion matches cubie move for all basic moves", () => {
    const moves = [
      "U",
      "D",
      "R",
      "L",
      "F",
      "B",
    ] as const;

    for (const move of moves) {
      const cube = new Cube();

      cube.move(move);

      const converted =
        CubieCube.fromCubeState(
          cube.getState()
        );

      const solved =
        new CubieCube();

      const expected =
        applyCubieMove(
          solved,
          move
        );

      console.log(`\n===== ${move} =====`);

      console.log("converted CP:", converted.cp);
      console.log("expected  CP:", expected.cp);

      console.log("converted EP:", converted.ep);
      console.log("expected  EP:", expected.ep);

      expect(converted.cp).toEqual(
        expected.cp
      );

      expect(converted.co).toEqual(
        expected.co
      );

      expect(converted.ep).toEqual(
        expected.ep
      );

      expect(converted.eo).toEqual(
        expected.eo
      );
    }
  });

});