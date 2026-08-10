import { CubieCube } from "../representation/CubieCube";
import {
  getEdgeOrientationIndex,
  buildEdgeOrientationTable,
} from "../tables/pruning";

const edgeOrientationTable =
  buildEdgeOrientationTable();

export function edgeHeuristic(
  cube: CubieCube
): number {
  const index =
    getEdgeOrientationIndex(cube);

  return edgeOrientationTable[index];
}