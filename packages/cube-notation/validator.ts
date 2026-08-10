const MOVE_PATTERN = /^[UDRLFB](?:'|2)?$/;

export interface NotationValidationResult {
  valid: boolean;
  invalidMoves: string[];
}

export function validateAlgorithm(
  input: string
): NotationValidationResult {
  const tokens = input
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  const invalidMoves = tokens.filter(
    (token) => !MOVE_PATTERN.test(token)
  );

  return {
    valid: invalidMoves.length === 0,
    invalidMoves,
  };
}