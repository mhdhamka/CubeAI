import { CubeState } from "../cube-core/CubeState";
import { Solver, SolveResult } from "./Solver";

export class KociembaSolver implements Solver {
  solve(state: CubeState): SolveResult {
    throw new Error(
      "Kociemba solver is not implemented yet."
    );
  }
}