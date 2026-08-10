import { CubieCube } from "./representation/CubieCube";
import { Move } from "../cube-core/Move";
import { Solver, SolveResult } from "./Solver";
import { heuristic } from "./heuristic/heuristic";
import { applyCubieMove } from "./tables/moveTables";

const MOVES: Move[] = [
  "U", "U'", "U2",
  "D", "D'", "D2",
  "R", "R'", "R2",
  "L", "L'", "L2",
  "F", "F'", "F2",
  "B", "B'", "B2",
];

const OPPOSITE: Record<string, string> = {
  U: "D",
  D: "U",
  R: "L",
  L: "R",
  F: "B",
  B: "F",
};

export class SearchSolver implements Solver {
  solve(state: any): SolveResult {
    const cube = CubieCube.fromCubeState(state);

    if (cube.isSolved()) {
      return {
        moves: [],
        moveCount: 0,
        solved: true,
      };
    }

    const path: Move[] = [];

    for (let depth = 1; depth <= 7; depth++) {
      const result = this.search(
        cube,
        depth,
        null,
        path
      );

      if (result !== null) {
        return {
          moves: result,
          moveCount: result.length,
          solved: true,
        };
      }
    }

    return {
      moves: [],
      moveCount: 0,
      solved: false,
    };
  }

  private search(
    cube: CubieCube,
    remainingDepth: number,
    previousFace: string | null,
    path: Move[]
  ): Move[] | null {
    if (cube.isSolved()) {
      return [...path];
    }

    const estimate = heuristic(cube);

    if (estimate > remainingDepth) {
      return null;
    }

    if (remainingDepth === 0) {
      return null;
    }

    for (const move of MOVES) {
      const face = move[0];

      if (previousFace !== null) {
        if (face === previousFace) {
          continue;
        }

        if (OPPOSITE[face] === previousFace) {
          continue;
        }
      }

      const nextCube = applyCubieMove(
        cube,
        move
      );

      path.push(move);

      const result = this.search(
        nextCube,
        remainingDepth - 1,
        face,
        path
      );

      path.pop();

      if (result !== null) {
        return result;
      }
    }

    return null;
  }
}