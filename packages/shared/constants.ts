import { CubeColor } from "../cube-core/CubeState";
import { FaceName } from "./types";

export const FACE_NAMES: readonly FaceName[] = [
  "U",
  "D",
  "F",
  "B",
  "L",
  "R",
] as const;

export const DEFAULT_RENDER_OPTIONS = {
  size: 300,
  stickerGap: 2,
  stickerRadius: 4,
} as const;

export const DEFAULT_FACE_COLORS: Record<
  CubeColor,
  string
> = {
  [CubeColor.White]: "#FFFFFF",
  [CubeColor.Yellow]: "#FFD500",
  [CubeColor.Red]: "#B71234",
  [CubeColor.Orange]: "#FF5800",
  [CubeColor.Green]: "#009B48",
  [CubeColor.Blue]: "#0046AD",
};