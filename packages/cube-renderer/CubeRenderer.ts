import {
  CubeState,
  CubeColor,
} from "../cube-core/CubeState";

import {
  DEFAULT_FACE_COLORS,
  DEFAULT_RENDER_OPTIONS,
} from "../shared/constants";

import {
  CubeRenderOptions,
  FaceName,
} from "../shared/types";

export class CubeRenderer {
  private options: Required<CubeRenderOptions>;

  constructor(
    options: CubeRenderOptions = {}
  ) {
    this.options = {
      ...DEFAULT_RENDER_OPTIONS,
      ...options,
    };
  }

  public render(state: CubeState): string {
    const size = this.options.size;

    const stickerSize =
      (size - this.options.stickerGap * 8) / 9;

    const svg = [
      `<svg`,
      `xmlns="http://www.w3.org/2000/svg"`,
      `width="${size}"`,
      `height="${size}"`,
      `viewBox="0 0 ${size} ${size}"`,
      `role="img"`,
      `aria-label="Rubik's Cube"`,
      `>`,
      `<rect width="100%" height="100%" fill="#111111"/>`,
    ];

    this.renderFace(
      svg,
      "U",
      state.U,
      size,
      stickerSize,
      3,
      0
    );

    this.renderFace(
      svg,
      "L",
      state.L,
      size,
      stickerSize,
      0,
      3
    );

    this.renderFace(
      svg,
      "F",
      state.F,
      size,
      stickerSize,
      3,
      3
    );

    this.renderFace(
      svg,
      "R",
      state.R,
      size,
      stickerSize,
      6,
      3
    );

    this.renderFace(
      svg,
      "B",
      state.B,
      size,
      stickerSize,
      9,
      3
    );

    this.renderFace(
      svg,
      "D",
      state.D,
      size,
      stickerSize,
      3,
      6
    );

    svg.push("</svg>");

    return svg.join("");
  }

  private renderFace(
    svg: string[],
    face: FaceName,
    stickers: CubeColor[],
    size: number,
    stickerSize: number,
    gridX: number,
    gridY: number
  ): void {
    for (let i = 0; i < 9; i++) {
      const row = Math.floor(i / 3);
      const col = i % 3;

      const x =
        (gridX + col) *
        (stickerSize + this.options.stickerGap);

      const y =
        (gridY + row) *
        (stickerSize + this.options.stickerGap);

      const color =
        DEFAULT_FACE_COLORS[stickers[i]];

      svg.push(
        `<rect`,
        `x="${x}"`,
        `y="${y}"`,
        `width="${stickerSize}"`,
        `height="${stickerSize}"`,
        `rx="${this.options.stickerRadius}"`,
        `fill="${color}"`,
        `stroke="#000000"`,
        `stroke-width="1"`,
        `data-face="${face}"`,
        `data-index="${i}"`,
        `/>`
      );
    }
  }
}