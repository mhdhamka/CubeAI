import { CubieCube } from "../representation/CubieCube";
import { Move } from "../../cube-core/Move";
import { applyCubieMove } from "./moveTables";

export interface PruningTable {
  get(key: number): number;
  set(key: number, depth: number): void;
}

export class SimplePruningTable
  implements PruningTable
{
  private table = new Map<number, number>();

  get(key: number): number {
    return this.table.get(key) ?? -1;
  }

  set(key: number, depth: number): void {
    this.table.set(key, depth);
  }
}


/*
 * ---------------------------------------------------------
 * Corner Orientation Index
 * ---------------------------------------------------------
 *
 * There are:
 *
 *   3^7 = 2187
 *
 * possible corner-orientation states.
 *
 * The eighth corner orientation is determined
 * by the first seven.
 */

export function getCornerOrientationIndex(
  cube: CubieCube
): number {
  let index = 0;

  for (let i = 0; i < 7; i++) {
    index =
      index * 3 +
      cube.co[i];
  }

  return index;
}


/*
 * ---------------------------------------------------------
 * Build Corner Orientation Pruning Table
 * ---------------------------------------------------------
 */

export function buildCornerOrientationTable(): number[] {
  const size = 2187;

  const table = new Array<number>(size).fill(-1);

  const solved = new CubieCube();

  const solvedIndex =
    getCornerOrientationIndex(solved);

  table[solvedIndex] = 0;

  const queue: CubieCube[] = [solved];

  let head = 0;

  const moves: Move[] = [
    "U", "U'", "U2",
    "D", "D'", "D2",
    "R", "R'", "R2",
    "L", "L'", "L2",
    "F", "F'", "F2",
    "B", "B'", "B2",
  ];

  while (head < queue.length) {
    const current = queue[head++];

    const currentIndex =
      getCornerOrientationIndex(current);

    const currentDepth =
      table[currentIndex];

    for (const move of moves) {
      const next =
        applyCubieMove(current, move);

      const nextIndex =
        getCornerOrientationIndex(next);

      if (table[nextIndex] !== -1) {
        continue;
      }

      table[nextIndex] =
        currentDepth + 1;

      queue.push(next);
    }
  }

  return table;
}


/*
 * ---------------------------------------------------------
 * Edge Orientation Index
 * ---------------------------------------------------------
 *
 * There are:
 *
 *   2^11 = 2048
 *
 * possible edge-orientation states.
 *
 * The twelfth edge orientation is determined
 * by the first eleven.
 */

export function getEdgeOrientationIndex(
  cube: CubieCube
): number {
  let index = 0;

  for (let i = 0; i < 11; i++) {
    index =
      index * 2 +
      cube.eo[i];
  }

  return index;
}


/*
 * ---------------------------------------------------------
 * Build Edge Orientation Pruning Table
 * ---------------------------------------------------------
 */

export function buildEdgeOrientationTable(): number[] {
  const size = 2048;

  const table = new Array<number>(size).fill(-1);

  const solved = new CubieCube();

  const solvedIndex =
    getEdgeOrientationIndex(solved);

  table[solvedIndex] = 0;

  const queue: CubieCube[] = [solved];

  let head = 0;

  const moves: Move[] = [
    "U",
    "D",
    "R",
    "L",
    "F",
    "B",
  ];

  while (head < queue.length) {
    const current = queue[head++];

    const currentIndex =
      getEdgeOrientationIndex(current);

    const currentDepth =
      table[currentIndex];

    for (const move of moves) {
      const next =
        applyCubieMove(current, move);

      const nextIndex =
        getEdgeOrientationIndex(next);

      if (table[nextIndex] !== -1) {
        continue;
      }

      table[nextIndex] =
        currentDepth + 1;

      queue.push(next);
    }
  }

  return table;
}