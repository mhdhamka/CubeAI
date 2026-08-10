import { Move } from "./Move";

const FACES = ["U", "D", "R", "L", "F", "B"] as const;
const MODIFIERS = ["", "'", "2"] as const;

export function generateScramble(length = 20): Move[] {
  const scramble: Move[] = [];
  let previousFace: string | null = null;

  while (scramble.length < length) {
    const face =
      FACES[Math.floor(Math.random() * FACES.length)];

    // Don't generate the same face twice in a row.
    if (face === previousFace) {
      continue;
    }

    const modifier =
      MODIFIERS[Math.floor(Math.random() * MODIFIERS.length)];

    scramble.push(`${face}${modifier}` as Move);
    previousFace = face;
  }

  return scramble;
}

export function scrambleToString(scramble: Move[]): string {
  return scramble.join(" ");
}