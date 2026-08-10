import { Move } from "../cube-core/Move";

export function formatAlgorithm(moves: Move[]): string {
  return moves.join(" ");
}