import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { APIError, CubeAIClient } from "../packages/cube-api/client";

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  fetchMock.mockReset();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("CubeAIClient", () => {
  it("sends typed solve requests to the API contract", async () => {
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          moves: [{ face: "R", times: 3 }],
          num_moves: 1,
          confidence: 1,
          solving_time_ms: 12,
          solver_used: "kociemba-two-phase",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    const client = new CubeAIClient({ baseUrl: "http://api.test" });
    const request = {
      cube_state: {
        faces: {
          U: [["W", "W", "W"], ["W", "W", "W"], ["W", "W", "W"]],
          R: [["R", "R", "R"], ["R", "R", "R"], ["R", "R", "R"]],
          F: [["G", "G", "G"], ["G", "G", "G"], ["G", "G", "G"]],
          D: [["Y", "Y", "Y"], ["Y", "Y", "Y"], ["Y", "Y", "Y"]],
          L: [["O", "O", "O"], ["O", "O", "O"], ["O", "O", "O"]],
          B: [["B", "B", "B"], ["B", "B", "B"], ["B", "B", "B"]],
        },
      },
      max_moves: 20,
    };

    const response = await client.solve(request);

    expect(response.moves[0]).toEqual({ face: "R", times: 3 });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/solve",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(request),
      }),
    );
  });

  it("uploads multiple images as repeated multipart files", async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const client = new CubeAIClient({ baseUrl: "http://api.test" });
    const files = [
      new File(["up"], "up.png", { type: "image/png" }),
      new File(["right"], "right.png", { type: "image/png" }),
    ];

    await client.scanImage(files);

    const [, request] = fetchMock.mock.calls[0];
    const form = request.body as FormData;
    expect(form.getAll("files")).toEqual(files);
    expect(request.headers ?? {}).not.toHaveProperty("Content-Type");
  });

  it("preserves structured server errors for the UI", async () => {
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          code: "INVALID_CUBE_STATE",
          message: "Two cube faces are missing",
          details: { missing_faces: ["U", "R"] },
        }),
        { status: 422, headers: { "Content-Type": "application/json" } },
      ),
    );
    const client = new CubeAIClient({ baseUrl: "http://api.test" });

    await expect(client.health()).rejects.toMatchObject<Partial<APIError>>({
      code: "INVALID_CUBE_STATE",
      message: "Two cube faces are missing",
      statusCode: 422,
      details: { missing_faces: ["U", "R"] },
    });
  });
});
