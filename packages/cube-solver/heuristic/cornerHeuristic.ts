import { CubieCube } from "../representation/CubieCube";
import {
  getCornerOrientationIndex,
  buildCornerOrientationTable,
} from "../tables/pruning";

const cornerOrientationTable =
  buildCornerOrientationTable();

export function cornerHeuristic(
  cube: CubieCube
): number {
  const index =
    getCornerOrientationIndex(cube);

  return cornerOrientationTable[index];
}