import { CubeState, CubeColor } from "./CubeState";

const COLORS: CubeColor[] = [
  CubeColor.White,
  CubeColor.Yellow,
  CubeColor.Green,
  CubeColor.Blue,
  CubeColor.Red,
  CubeColor.Orange,
];

export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

export function validateCube(
  state: CubeState
): ValidationResult {
  const errors: string[] = [];

  const counts = new Map<CubeColor, number>();

  for (const color of COLORS) {
    counts.set(color, 0);
  }

  for (const face of Object.values(state)) {
    for (const color of face) {
      counts.set(
        color,
        (counts.get(color) ?? 0) + 1
      );
    }
  }

  for (const color of COLORS) {
    const count = counts.get(color) ?? 0;

    if (count !== 9) {
      errors.push(
        `Color ${color} appears ${count} times; expected 9.`
      );
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}