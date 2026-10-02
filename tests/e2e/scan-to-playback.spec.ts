import { expect, test } from "@playwright/test";
import { Cube } from "../../packages/cube-core/Cube";
import type { CubeColor } from "../../packages/cube-core/CubeState";

test("uploads six face images, solves through Python, and plays the returned solution", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("header")).toContainText("API connected");

  const cube = new Cube();
  cube.applyMoves(["R", "U", "F"]);
  const stickerFaces = cube.getState();
  const files = await page.evaluate(async (faceMap) => {
    const colorMap: Record<string, string> = {
      W: "#ffffff",
      Y: "#ffff00",
      R: "#ff0000",
      O: "#ff8800",
      G: "#00aa00",
      B: "#0000ff",
    };
    return await Promise.all(
      Object.entries(faceMap).map(([face, stickers]) => {
        const canvas = document.createElement("canvas");
        canvas.width = 600;
        canvas.height = 600;
        const context = canvas.getContext("2d");
        if (!context) throw new Error("Canvas is unavailable");
        context.fillStyle = "#ffffff";
        context.fillRect(0, 0, 600, 600);
        stickers.forEach((color, index) => {
          const row = Math.floor(index / 3);
          const column = index % 3;
          const x = 60 + column * 160;
          const y = 60 + row * 160;
          context.fillStyle = "#111111";
          context.fillRect(x, y, 140, 140);
          context.fillStyle = colorMap[String(color)];
          context.fillRect(x + 8, y + 8, 124, 124);
        });
        return { name: `${face}.png`, dataUrl: canvas.toDataURL("image/png") };
      }),
    );
  }, stickerFaces as unknown as Record<string, CubeColor[]>);

  await page.getByRole("button", { name: "scanner" }).click();
  await page.getByLabel("Choose face photos").setInputFiles(
    files.map(({ name, dataUrl }) => ({
      name,
      mimeType: "image/png",
      buffer: Buffer.from(dataUrl.split(",")[1], "base64"),
    })),
  );
  await page.getByRole("button", { name: "Scan and solve" }).click();

  await expect(
    page.getByRole("heading", { name: "Solution interface" }),
  ).toBeVisible({ timeout: 60_000 });
  await expect(page.locator("header")).toContainText(/Scanned 6 faces at \d+% confidence/);
  await page.getByRole("button", { name: "Visualize solution" }).click();
  await expect(page.getByRole("heading", { name: "Interactive model" })).toBeVisible();
  await expect(page.locator("canvas").first()).toBeVisible();

  const playback = page.locator('[aria-live="polite"]');
  await page.getByRole("button", { name: "Play solution" }).click();
  await expect(playback).toHaveText(/\d+ \/ \d+/, { timeout: 15_000 });
});