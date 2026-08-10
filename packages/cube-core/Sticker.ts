import { CubeColor, CubeFace } from "./CubeState";

export interface Sticker {
  color: CubeColor;
  face: CubeFace;
  index: number;
}