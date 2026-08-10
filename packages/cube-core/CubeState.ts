export enum CubeColor {
  White = "W",
  Yellow = "Y",
  Green = "G",
  Blue = "B",
  Red = "R",
  Orange = "O",
}

export enum CubeFace {
  Up = "U",
  Right = "R",
  Front = "F",
  Down = "D",
  Left = "L",
  Back = "B",
}

export type FaceStickers = [
  CubeColor,
  CubeColor,
  CubeColor,
  CubeColor,
  CubeColor,
  CubeColor,
  CubeColor,
  CubeColor,
  CubeColor
];

export interface CubeState {
  U: FaceStickers;
  R: FaceStickers;
  F: FaceStickers;
  D: FaceStickers;
  L: FaceStickers;
  B: FaceStickers;
}