import {
  CubeColor,
  CubeState,
  FaceStickers,
} from "./CubeState";

export function createSolvedFace(
  color: CubeColor
): FaceStickers {
  return [
    color,
    color,
    color,
    color,
    color,
    color,
    color,
    color,
    color,
  ];
}

export function createSolvedState(): CubeState {
  return {
    U: createSolvedFace(CubeColor.White),
    R: createSolvedFace(CubeColor.Red),
    F: createSolvedFace(CubeColor.Green),
    D: createSolvedFace(CubeColor.Yellow),
    L: createSolvedFace(CubeColor.Orange),
    B: createSolvedFace(CubeColor.Blue),
  };
}

export function rotateFaceClockwise(
  face: FaceStickers
): FaceStickers {
  return [
    face[6],
    face[3],
    face[0],
    face[7],
    face[4],
    face[1],
    face[8],
    face[5],
    face[2],
  ];
}

export function rotateFaceCounterClockwise(
  face: FaceStickers
): FaceStickers {
  return [
    face[2],
    face[5],
    face[8],
    face[1],
    face[4],
    face[7],
    face[0],
    face[3],
    face[6],
  ];
}