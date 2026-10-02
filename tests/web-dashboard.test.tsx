// @vitest-environment jsdom

import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import Home from "../apps/web/app/page";
import { apiClient, APIError } from "../packages/cube-api/client";

vi.mock("../packages/cube-api/client", () => ({
  APIError: class extends Error {
    code: string;
    statusCode: number;
    details?: Record<string, unknown>;
    constructor(code: string, message: string, statusCode: number, details?: Record<string, unknown>) {
      super(message);
      this.code = code;
      this.statusCode = statusCode;
      this.details = details;
    }
  },
  apiClient: {
    getOrCreateGuestProfile: vi.fn(),
    getSolves: vi.fn(),
    getStatistics: vi.fn(),
    getTrainingAttempts: vi.fn(),
    validate: vi.fn(),
    solve: vi.fn(),
    scanImage: vi.fn(),
    createSolve: vi.fn(),
    createTrainingAttempt: vi.fn(),
    getCoaching: vi.fn(),
  },
}));

vi.mock("../packages/cube-renderer/CubePlayer", () => ({
  CubePlayer: () => <div aria-label="3D cube preview" />,
}));

afterEach(cleanup);

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(apiClient.getOrCreateGuestProfile).mockResolvedValue({
    id: 1,
    user_id: 1,
    name: "Cube Lab",
  });
  vi.mocked(apiClient.getSolves).mockResolvedValue([]);
  vi.mocked(apiClient.getStatistics).mockResolvedValue({
    profile_id: 1,
    total_solves: 0,
    best_time_ms: null,
    worst_time_ms: null,
    average_ao5_ms: null,
    average_ao12_ms: null,
    average_ao100_ms: null,
    average_overall_ms: null,
  });
  vi.mocked(apiClient.getTrainingAttempts).mockResolvedValue([]);
  vi.mocked(apiClient.validate).mockResolvedValue({
    valid: true,
    errors: [],
    is_solved: false,
    scramble_distance: 3,
  });
  vi.mocked(apiClient.solve).mockResolvedValue({
    moves: [{ face: "R", times: 3 }],
    num_moves: 1,
    confidence: 1,
    solving_time_ms: 3,
    solver_used: "kociemba-two-phase",
  });
});

describe("Cube Lab dashboard", () => {
  it("shows the scanner view after choosing Scanner", () => {
    render(<Home />);

    expect(screen.getByRole("main")).toHaveClass("min-h-screen", "bg-paper");
    fireEvent.click(screen.getByRole("button", { name: "scanner" }));

    expect(
      screen.getByRole("heading", { name: "Bring a cube into the lab" }),
    ).toBeInTheDocument();
  });

  it("applies the selected color to a sticker", () => {
    render(<Home />);

    fireEvent.click(screen.getByRole("button", { name: "Set Yellow" }));
    fireEvent.click(
      screen.getByRole("button", { name: "U sticker 1: White" }),
    );

    expect(
      screen.getByRole("button", { name: "U sticker 1: Yellow" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("validates and solves the current sticker state through the API", async () => {
    render(<Home />);

    fireEvent.click(screen.getByRole("button", { name: "Set Yellow" }));
    fireEvent.click(screen.getByRole("button", { name: "U sticker 1: White" }));
    fireEvent.click(screen.getByRole("button", { name: /Find solution/ }));

    await screen.findByText("The API returned a verified 1-move solution.");
    expect(apiClient.validate).toHaveBeenCalledWith({
      cube_state: expect.objectContaining({
        faces: expect.objectContaining({
          U: [["Y", "W", "W"], ["W", "W", "W"], ["W", "W", "W"]],
        }),
      }),
    });
    expect(apiClient.solve).toHaveBeenCalledWith(
      expect.objectContaining({ cube_state: expect.any(Object) }),
    );
    expect(screen.getByText("R'", { selector: "div" })).toBeInTheDocument();
  });

  it("uploads selected face images and solves the returned scanned state", async () => {
    const files = ["U", "R", "F", "D", "L", "B"].map(
      (face) => new File([face], `${face}.png`, { type: "image/png" }),
    );
    vi.mocked(apiClient.scanImage).mockResolvedValue({
      cube_state: {
        corners: [0, 1, 2, 3, 4, 5, 6, 7],
        corner_orientations: [0, 0, 0, 0, 0, 0, 0, 0],
        edges: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        edge_orientations: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      },
      faces: {
        U: Array.from({ length: 3 }, () => Array(3).fill("white")),
        R: Array.from({ length: 3 }, () => Array(3).fill("red")),
        F: Array.from({ length: 3 }, () => Array(3).fill("green")),
        D: Array.from({ length: 3 }, () => Array(3).fill("yellow")),
        L: Array.from({ length: 3 }, () => Array(3).fill("orange")),
        B: Array.from({ length: 3 }, () => Array(3).fill("blue")),
      },
      metadata: {
        confidence: 0.98,
        detected_faces: 6,
        processing_time_ms: 20,
        model_version: "test",
      },
      validation: {
        valid: true,
        errors: [],
        is_solved: true,
        scramble_distance: 0,
      },
    });

    render(<Home />);
    fireEvent.click(screen.getByRole("button", { name: "scanner" }));
    fireEvent.change(screen.getByLabelText("Choose face photos"), {
      target: { files },
    });
    fireEvent.click(screen.getByRole("button", { name: "Scan and solve" }));

    await screen.findByRole("heading", { name: "Solution interface" });
    expect(apiClient.scanImage).toHaveBeenCalledWith(files);
    expect(apiClient.solve).toHaveBeenCalledWith({
      cube_state: expect.objectContaining({ corners: expect.any(Array) }),
    });
    expect(screen.getByRole("banner")).toHaveTextContent(
      "Scanned 6 faces at 98% confidence",
    );
  });

  it("shows API errors and offers a retry", async () => {
    vi.mocked(apiClient.getOrCreateGuestProfile).mockRejectedValueOnce(
      new APIError("NETWORK_ERROR", "API is unreachable", 0),
    );

    render(<Home />);

    expect(await screen.findByRole("alert")).toHaveTextContent("API is unreachable");
    expect(screen.getByRole("button", { name: "Retry connection" })).toBeEnabled();
  });

  it("saves timer attempts with the selected +2 penalty", async () => {
    vi.mocked(apiClient.createSolve).mockResolvedValue({
      id: 10,
      profile_id: 1,
      time_ms: 1000,
      penalty_ms: 2000,
      num_moves: 1,
      scramble: "Manual cube solve",
      solution: "Timed solve",
      is_dnf: false,
      is_dns: false,
    });
    render(<Home />);
    await waitFor(() =>
      expect(screen.getByRole("banner")).toHaveTextContent("API connected"),
    );

    fireEvent.click(screen.getByRole("button", { name: "timer" }));
    fireEvent.change(screen.getByLabelText("Result penalty"), {
      target: { value: "plus2" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start solve" }));
    fireEvent.click(screen.getByRole("button", { name: "Stop and save" }));

    await waitFor(() => expect(apiClient.createSolve).toHaveBeenCalled());
    expect(apiClient.createSolve).toHaveBeenCalledWith(
      expect.objectContaining({ penalty_ms: 2000, is_dnf: false }),
    );
  });

  it("records recognition and execution times for algorithm training", async () => {
    vi.mocked(apiClient.createTrainingAttempt).mockResolvedValue({
      id: 4,
      profile_id: 1,
      algorithm: "R U R' U'",
      recognition_time_ms: 12,
      execution_time_ms: 8,
      was_correct: true,
    });
    render(<Home />);
    await waitFor(() =>
      expect(screen.getByRole("banner")).toHaveTextContent("API connected"),
    );

    fireEvent.click(screen.getByRole("button", { name: "training" }));
    fireEvent.click(screen.getByRole("button", { name: "Start recognition" }));
    fireEvent.click(screen.getByRole("button", { name: "Recognized" }));
    fireEvent.click(screen.getByRole("button", { name: "Complete rep" }));

    await waitFor(() => expect(apiClient.createTrainingAttempt).toHaveBeenCalled());
    expect(apiClient.createTrainingAttempt).toHaveBeenCalledWith(
      expect.objectContaining({
        profile_id: 1,
        algorithm: "R U R' U'",
        recognition_time_ms: expect.any(Number),
        execution_time_ms: expect.any(Number),
      }),
    );
  });

  it("requests contextual coaching for the selected focus", async () => {
    vi.mocked(apiClient.getCoaching).mockResolvedValue({
      explanation: "Pair the corner and edge before inserting them.",
      key_points: ["Look for matching colors"],
      suggested_algorithms: ["R U R' U'"],
      difficulty_level: "beginner",
    });
    render(<Home />);

    fireEvent.click(screen.getByRole("button", { name: "coaching" }));
    fireEvent.change(screen.getByLabelText("Focus"), {
      target: { value: "f2l" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Get coaching" }));

    expect(await screen.findByText("Pair the corner and edge before inserting them.")).toBeInTheDocument();
    expect(apiClient.getCoaching).toHaveBeenCalledWith(
      expect.objectContaining({ focus: "f2l" }),
    );
  });
});