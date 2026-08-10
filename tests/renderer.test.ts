import {
  describe,
  expect,
  test,
} from "vitest";

import { Cube } from "../packages/cube-core/Cube";
import { CubeRenderer } from "../packages/cube-renderer/CubeRenderer";

describe("CubeRenderer", () => {
  test("renders solved cube as SVG", () => {
    const cube = new Cube();
    const renderer = new CubeRenderer();

    const svg = renderer.render(
      cube.getState()
    );

    expect(svg).toContain("<svg");
    expect(svg).toContain("</svg>");
  });

  test("renders all 54 stickers", () => {
    const cube = new Cube();
    const renderer = new CubeRenderer();

    const svg = renderer.render(
      cube.getState()
    );

    const stickerCount =
      (svg.match(/data-face=/g) ?? []).length;

    expect(stickerCount).toBe(54);
  });

  test("renders a scrambled cube", () => {
    const cube = new Cube();

    cube.applyMoves([
      "R",
      "U",
      "F",
    ]);

    const renderer = new CubeRenderer();

    const svg = renderer.render(
      cube.getState()
    );

    expect(svg).toContain("<svg");
    expect(svg).toContain("data-face=");
  });
});