import { CubieCube } from "../representation/CubieCube";
import { cornerHeuristic } from "./cornerHeuristic";
import { edgeHeuristic } from "./edgeHeuristic";

export function heuristic(
  cube: CubieCube
  ): number {
    return Math.max(
      cornerHeuristic(cube),
      edgeHeuristic(cube)
    );
  }