export type FaceMove = "U" | "D" | "R" | "L" | "F" | "B";

export type MoveModifier = "" | "'" | "2";

export type Move = `${FaceMove}${MoveModifier}`;