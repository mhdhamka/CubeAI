import { CubeState } from "../cube-core/CubeState";
import { Move } from "../cube-core/Move";

export interface SolveResult {
  moves: Move[];
  moveCount: number;
  solved: boolean;
}

export interface Solver {
  solve(state: CubeState): SolveResult;
}