import { Move } from "../cube-core/Move";

const MOVE_PATTERN = /^[UDRLFB](?:'|2)?$/;

export function parseAlgorithm(input: string): Move[] {
  const tokens = input
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  for (const token of tokens) {
    if (!MOVE_PATTERN.test(token)) {
      throw new Error(`Invalid move notation: ${token}`);
    }
  }

  return tokens as Move[];
}