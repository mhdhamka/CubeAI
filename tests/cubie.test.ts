import { describe, expect, test } from "vitest";

import { Cube } from "../packages/cube-core/Cube";
import { CubieCube } from "../packages/cube-solver/representation/CubieCube";
import {
  applyCubieMove,
} from "../packages/cube-solver/tables/moveTables";

import {
  getCornerOrientationIndex,
  buildCornerOrientationTable,
} from "../packages/cube-solver/tables/pruning";

import {
  getEdgeOrientationIndex,
  buildEdgeOrientationTable,
} from "../packages/cube-solver/tables/pruning";

const FACES = [
  "U",
  "D",
  "R",
  "L",
  "F",
  "B",
] as const;

describe("CubieCube", () => {
  test("converts solved CubeState to solved CubieCube", () => {
    const cube = new Cube();

    const cubie = CubieCube.fromCubeState(
      cube.getState()
    );

    expect(cubie.isSolved()).toBe(true);
  });
});

describe("Cubie move tables", () => {
  test.each(FACES)(
    "%s four times returns solved",
    (move) => {
      const cube = new CubieCube();

      const once =
        applyCubieMove(cube, move);

      const twice =
        applyCubieMove(once, move);

      const three =
        applyCubieMove(twice, move);

      const four =
        applyCubieMove(three, move);

      expect(four.isSolved()).toBe(true);
    }
  );

  describe("Corner orientation pruning", () => {
    test("solved cube has orientation index 0", () => {
        const cube = new CubieCube();

        expect(
        getCornerOrientationIndex(cube)
        ).toBe(0);
    });

    test("corner orientation index stays within range", () => {
        const cube = new CubieCube();

        const index =
        getCornerOrientationIndex(cube);

        expect(index).toBeGreaterThanOrEqual(0);
        expect(index).toBeLessThan(2187);
    });

    test("builds all corner orientation states", () => {
        const table =
        buildCornerOrientationTable();

        expect(table).toHaveLength(2187);

        expect(
        table.every((depth) => depth !== -1)
        ).toBe(true);
    });
  });

  describe("Edge orientation pruning", () => {
    test("solved cube has edge orientation index 0", () => {
        const cube = new CubieCube();

        expect(
        getEdgeOrientationIndex(cube)
        ).toBe(0);
    });

    test("edge orientation index stays within range", () => {
        const cube = new CubieCube();

        const index =
        getEdgeOrientationIndex(cube);

        expect(index).toBeGreaterThanOrEqual(0);
        expect(index).toBeLessThan(2048);
    });

    test("builds all edge orientation states", () => {
        const table =
        buildEdgeOrientationTable();

        expect(table).toHaveLength(2048);

        expect(
        table.every((depth) => depth !== -1)
        ).toBe(true);
    });
  });

  test.each(FACES)(
    "%s followed by its inverse returns solved",
    (move) => {
      const cube = new CubieCube();

      const once =
        applyCubieMove(cube, move);

      const inverse =
        move === "U" ? "U'" :
        move === "D" ? "D'" :
        move === "R" ? "R'" :
        move === "L" ? "L'" :
        move === "F" ? "F'" :
        "B'";

      const result =
        applyCubieMove(once, inverse);

      expect(result.isSolved()).toBe(true);
    }
  );
});