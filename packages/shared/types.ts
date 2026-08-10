import { CubeColor } from "../cube-core/CubeState";
import { Move } from "../cube-core/Move";

export type FaceName =
  | "U"
  | "D"
  | "F"
  | "B"
  | "L"
  | "R";

export type CubeColors = Record<
  FaceName,
  CubeColor[]
>;

export interface CubeRenderOptions {
  size?: number;
  stickerGap?: number;
  stickerRadius?: number;
}

export interface RenderMove {
  move: Move;
  duration?: number;
}