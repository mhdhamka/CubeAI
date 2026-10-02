"use client";

import { useEffect, useRef, useState } from "react";
import { Cube } from "../../../packages/cube-core/Cube";
import type { Move } from "../../../packages/cube-core/Move";
import { CubePlayer } from "../../../packages/cube-renderer/CubePlayer";
import { CubeColor } from "../../../packages/cube-core/CubeState";
import type { CubeState, FaceStickers } from "../../../packages/cube-core/CubeState";
import { APIError, apiClient } from "../../../packages/cube-api/client";
import { useScanSession } from "../../../packages/cube-api/hooks-websocket";
import type {
  Profile,
  SolveRecord,
  StickerCubeState,
  Statistics,
  TrainingAttempt,
  CoachingResponse,
} from "../../../packages/cube-api/types";
import {
  ActionButton,
  Panel,
  SectionLabel,
} from "./components/dashboard-primitives";

const FACE_NAMES = ["U", "R", "F", "D", "L", "B"] as const;
const COLORS = [
  CubeColor.White,
  CubeColor.Yellow,
  CubeColor.Red,
  CubeColor.Orange,
  CubeColor.Green,
  CubeColor.Blue,
];
const COLOR_NAMES: Record<CubeColor, string> = {
  W: "White",
  Y: "Yellow",
  R: "Red",
  O: "Orange",
  G: "Green",
  B: "Blue",
};
const COLOR_CODES: Record<string, CubeColor> = {
  white: CubeColor.White,
  yellow: CubeColor.Yellow,
  red: CubeColor.Red,
  orange: CubeColor.Orange,
  green: CubeColor.Green,
  blue: CubeColor.Blue,
};
type View =
  | "dashboard"
  | "scanner"
  | "solver"
  | "cube"
  | "timer"
  | "training"
  | "coaching"
  | "statistics"
  | "profile";

const toStickerCubeState = (state: CubeState): StickerCubeState => ({
  faces: Object.fromEntries(
    FACE_NAMES.map((face) => [
      face,
      [0, 1, 2].map((row) =>
        Array.from(state[face].slice(row * 3, row * 3 + 3)),
      ),
    ]),
  ) as StickerCubeState["faces"],
});

const toFaceStickers = (face: string[][]): FaceStickers => {
  const colors = face.flat().map((color) => COLOR_CODES[color.toLowerCase()]);
  return [
    colors[0], colors[1], colors[2],
    colors[3], colors[4], colors[5],
    colors[6], colors[7], colors[8],
  ];
};

const fromStickerCubeState = (
  faces: StickerCubeState["faces"],
): CubeState => ({
  U: toFaceStickers(faces.U),
  R: toFaceStickers(faces.R),
  F: toFaceStickers(faces.F),
  D: toFaceStickers(faces.D),
  L: toFaceStickers(faces.L),
  B: toFaceStickers(faces.B),
});

const apiErrorMessage = (error: unknown): string => {
  if (error instanceof APIError) {
    const missingFaces = error.details?.missing_faces;
    if (Array.isArray(missingFaces) && missingFaces.length > 0) {
      return `${error.message}. Missing faces: ${missingFaces.join(", ")}.`;
    }
    return error.message;
  }
  return error instanceof Error ? error.message : "Unexpected API error";
};

export default function Home() {
  const [state, setState] = useState<CubeState>(() => new Cube().getState());
  const [solution, setSolution] = useState<Move[]>([]);
  const [message, setMessage] = useState("Ready to explore");
  const [view, setView] = useState<View>("dashboard");
  const [moveHistory, setMoveHistory] = useState<Move[]>([]);
  const [editFace, setEditFace] = useState<keyof CubeState>("U");
  const [editColor, setEditColor] = useState<CubeColor>(CubeColor.White);
  const [timerRunning, setTimerRunning] = useState(false);
  const [timerStarted, setTimerStarted] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [records, setRecords] = useState<SolveRecord[]>([]);
  const [trainingAttempts, setTrainingAttempts] = useState<TrainingAttempt[]>([]);
  const [trainingStartedAt, setTrainingStartedAt] = useState<number | null>(null);
  const [trainingRecognitionMs, setTrainingRecognitionMs] = useState<number | null>(null);
  const [trainingSaving, setTrainingSaving] = useState(false);
  const [coachingFocus, setCoachingFocus] = useState<"cross" | "f2l" | "oll" | "pll" | "overall">("overall");
  const [coachingResult, setCoachingResult] = useState<CoachingResponse | null>(null);
  const [coachingLoading, setCoachingLoading] = useState(false);
  const [solvePenalty, setSolvePenalty] = useState<"none" | "plus2" | "dnf">("none");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [apiLoading, setApiLoading] = useState(true);
  const [apiRetry, setApiRetry] = useState(0);
  const [solveLoading, setSolveLoading] = useState(false);
  const [scanLoading, setScanLoading] = useState(false);
  const [scanFiles, setScanFiles] = useState<File[]>([]);
  const [cameraActive, setCameraActive] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsBaseUrl =
    process.env.NEXT_PUBLIC_WS_URL ||
    (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(
      /^http/,
      "ws",
    );
  const scanSession = useScanSession(`${wsBaseUrl}/api/scan/session`, cameraActive);

  useEffect(() => {
    let mounted = true;
    const loadProfileData = async () => {
      setApiLoading(true);
      setApiError(null);
      try {
        const loadedProfile = await apiClient.getOrCreateGuestProfile();
        if (!loadedProfile.id) throw new Error("The API returned a profile without an ID");
        const [savedRecords, savedStatistics, savedTraining] = await Promise.all([
          apiClient.getSolves(loadedProfile.id),
          apiClient.getStatistics(loadedProfile.id),
          apiClient.getTrainingAttempts(loadedProfile.id),
        ]);
        if (!mounted) return;
        setProfile(loadedProfile);
        setRecords(savedRecords);
        setStatistics(savedStatistics);
        setTrainingAttempts(savedTraining);
        setMessage((current) =>
          current === "Ready to explore" ? "API connected · profile synced" : current,
        );
      } catch (error) {
        if (!mounted) return;
        setApiError(apiErrorMessage(error));
        setMessage("API unavailable");
      } finally {
        if (mounted) setApiLoading(false);
      }
    };
    void loadProfileData();
    return () => {
      mounted = false;
    };
  }, [apiRetry]);

  useEffect(() => {
    if (!cameraActive) return;
    let active = true;
    let stream: MediaStream | null = null;
    let captureTimer = 0;

    const startCamera = async () => {
      try {
        if (!navigator.mediaDevices?.getUserMedia) {
          throw new Error("Camera capture requires HTTPS or localhost in a supported browser.");
        }
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
          audio: false,
        });
        if (!active || !videoRef.current) return;
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        captureTimer = window.setInterval(() => {
          const video = videoRef.current;
          const canvas = canvasRef.current;
          const context = canvas?.getContext("2d");
          if (!video || !canvas || !context || video.videoWidth === 0) return;
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          context.drawImage(video, 0, 0, canvas.width, canvas.height);
          canvas.toBlob(async (blob) => {
            if (!blob || !active) return;
            scanSession.sendFrame(await blob.arrayBuffer());
          }, "image/jpeg", 0.88);
        }, 1200);
      } catch (error) {
        if (!active) return;
        setApiError(apiErrorMessage(error));
        setCameraActive(false);
      }
    };

    void startCamera();
    return () => {
      active = false;
      window.clearInterval(captureTimer);
      stream?.getTracks().forEach((track) => track.stop());
      if (videoRef.current) videoRef.current.srcObject = null;
    };
  }, [cameraActive, scanSession.sendFrame]);

  useEffect(() => {
    if (!cameraActive || !scanSession.cubeState || !scanSession.faces) return;
    let active = true;
    setCameraActive(false);
    setState(fromStickerCubeState(scanSession.faces));
    setSolveLoading(true);
    setApiError(null);
    void apiClient
      .solve({ cube_state: scanSession.cubeState })
      .then((result) => {
        if (!active) return;
        setSolution(
          result.moves.map(({ face, times }) =>
            `${face}${times === 1 ? "" : times === 2 ? "2" : "'"}` as Move,
          ),
        );
        setMessage(`Live scan verified · ${result.num_moves}-move solution`);
        setView("solver");
      })
      .catch((error) => setApiError(apiErrorMessage(error)))
      .finally(() => setSolveLoading(false));
    return () => {
      active = false;
    };
  }, [cameraActive, scanSession.cubeState, scanSession.faces]);

  useEffect(() => {
    if (!timerRunning) return;
    const interval = window.setInterval(
      () => setElapsed(Date.now() - timerStarted),
      30,
    );
    return () => window.clearInterval(interval);
  }, [timerRunning, timerStarted]);

  useEffect(() => {
    const handleKey = (event: KeyboardEvent) => {
      if (event.code !== "Space" || event.target instanceof HTMLInputElement) return;
      event.preventDefault();
      toggleTimer();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  });

  const applyMove = (move: Move) => {
    const next = new Cube(state);
    next.move(move);
    setState(next.getState());
    setMoveHistory((history) => [...history, move]);
    setMessage(`${move} applied`);
  };

  const scramble = () => {
    const next = new Cube();
    const moves: Move[] = ["R", "U", "F", "L'", "D2", "B", "R2"];
    next.applyMoves(moves);
    setState(next.getState());
    setMoveHistory(moves);
    setMessage("Scrambled cube loaded");
  };

  const reset = () => {
    setState(new Cube().getState());
    setMoveHistory([]);
    setMessage("Cube reset");
  };

  const solve = async () => {
    setSolveLoading(true);
    setApiError(null);
    try {
      const cubeState = toStickerCubeState(state);
      const validation = await apiClient.validate({ cube_state: cubeState });
      if (!validation.valid) {
        throw new Error(validation.errors.map((item) => item.error).join("; "));
      }
      const result = await apiClient.solve({ cube_state: cubeState });
      setSolution(
        result.moves.map(({ face, times }) =>
          `${face}${times === 1 ? "" : times === 2 ? "2" : "'"}` as Move,
        ),
      );
      setMessage(`Verified ${result.num_moves}-move ${result.solver_used} solution`);
      setView("solver");
    } catch (error) {
      setApiError(apiErrorMessage(error));
      setMessage("Solve request failed");
    } finally {
      setSolveLoading(false);
    }
  };

  const scanAndSolve = async () => {
    if (scanFiles.length === 0) {
      setApiError("Select cube-face images to scan.");
      return;
    }
    setScanLoading(true);
    setApiError(null);
    try {
      const scan = await apiClient.scanImage(scanFiles);
      if (!scan.validation.valid) {
        throw new Error(scan.validation.errors.map((item) => item.error).join("; "));
      }
      if (!scan.faces) throw new Error("The scan response did not include face colors");
      setState(fromStickerCubeState(scan.faces));
      setMoveHistory([]);
      const result = await apiClient.solve({ cube_state: scan.cube_state });
      setSolution(
        result.moves.map(({ face, times }) =>
          `${face}${times === 1 ? "" : times === 2 ? "2" : "'"}` as Move,
        ),
      );
      setMessage(
        `Scanned ${scan.metadata.detected_faces} faces at ${Math.round(scan.metadata.confidence * 100)}% confidence`,
      );
      setView("solver");
    } catch (error) {
      setApiError(apiErrorMessage(error));
      setMessage("Scan or solve request failed");
    } finally {
      setScanLoading(false);
    }
  };

  const toggleTimer = async () => {
    if (timerRunning) {
      const time = Date.now() - timerStarted;
      setElapsed(time);
      setTimerRunning(false);
      if (!profile?.id) {
        setApiError("A connected profile is required to save this solve.");
        return;
      }
      try {
        const saved = await apiClient.createSolve({
          profile_id: profile.id,
          time_ms: time,
          num_moves: Math.max(1, moveHistory.length),
          scramble: moveHistory.join(" ") || "Manual cube solve",
          solution: solution.join(" ") || "Timed solve",
          solver_used: "manual",
          confidence: 1,
          penalty_ms: solvePenalty === "plus2" ? 2000 : 0,
          is_dnf: solvePenalty === "dnf",
          is_dns: false,
        });
        setRecords((current) => [saved, ...current].slice(0, 100));
        setStatistics(await apiClient.getStatistics(profile.id));
        setApiError(null);
        setMessage("Solve saved to your profile");
      } catch (error) {
        setApiError(apiErrorMessage(error));
        setMessage("Could not save solve");
      }
    } else {
      setElapsed(0);
      setTimerStarted(Date.now());
      setTimerRunning(true);
    }
  };

  const finishTrainingAttempt = async () => {
    if (!profile?.id || trainingStartedAt === null || trainingRecognitionMs === null) {
      return;
    }
    setTrainingSaving(true);
    try {
      const attempt = await apiClient.createTrainingAttempt({
        profile_id: profile.id,
        algorithm: "R U R' U'",
        recognition_time_ms: trainingRecognitionMs,
        execution_time_ms: Math.max(0, Date.now() - trainingStartedAt - trainingRecognitionMs),
        was_correct: true,
      });
      setTrainingAttempts((current) => [attempt, ...current]);
      setTrainingStartedAt(null);
      setTrainingRecognitionMs(null);
      setMessage("Training attempt saved");
      setApiError(null);
    } catch (error) {
      setApiError(apiErrorMessage(error));
    } finally {
      setTrainingSaving(false);
    }
  };

  const requestCoaching = async () => {
    setCoachingLoading(true);
    setApiError(null);
    try {
      const result = await apiClient.getCoaching({
        cube_state: toStickerCubeState(state),
        focus: coachingFocus,
        solution_moves: solution.map((notation) => ({
          face: notation[0] as "U" | "D" | "F" | "B" | "L" | "R",
          times: notation.endsWith("2") ? 2 : notation.endsWith("'") ? 3 : 1,
        })),
      });
      setCoachingResult(result);
    } catch (error) {
      setApiError(apiErrorMessage(error));
    } finally {
      setCoachingLoading(false);
    }
  };

  const editSticker = (index: number, color: CubeColor) => {
    const next = new Cube(state).getState();
    next[editFace] = [
      ...next[editFace].slice(0, index),
      color,
      ...next[editFace].slice(index + 1),
    ] as (typeof next)[typeof editFace];
    setState(next);
    setMessage(`${editFace} sticker ${index + 1} updated`);
  };

  const formatTime = (milliseconds: number) =>
    `${Math.floor(milliseconds / 60000)}:${String(Math.floor(milliseconds / 1000) % 60).padStart(2, "0")}.${String(Math.floor(milliseconds % 1000)).padStart(3, "0")}`;
  const average = (count: number) => {
    const value =
      count === 5
        ? statistics?.average_ao5_ms
        : count === 12
          ? statistics?.average_ao12_ms
          : statistics?.average_ao100_ms;
    return value == null ? "--" : formatTime(value);
  };

  return (
    <main className="min-h-screen bg-paper bg-[radial-gradient(circle_at_8%_9%,#fff_0_2px,transparent_3px),linear-gradient(135deg,rgba(255,255,255,.7),transparent_42%)] bg-size-[22px_22px,auto] px-5 pb-12 pt-[34px] text-ink sm:px-[5vw] lg:px-[76px]">
      <nav className="mx-auto mb-11 flex max-w-[1280px] flex-col gap-5 border-b border-line pb-[18px] min-[851px]:flex-row min-[851px]:items-center min-[851px]:gap-7">
        <div className="flex items-center gap-[9px] whitespace-nowrap">
          <span className="text-[22px] text-orange">✦</span>
          <strong>CUBE / LAB</strong>
          <small className="font-mono text-[10px] text-muted">practice OS</small>
        </div>
        <div className="flex flex-1 flex-wrap gap-1.5">
          {(
            [
              "dashboard",
              "scanner",
              "solver",
              "cube",
              "timer",
              "training",
              "coaching",
              "statistics",
              "profile",
            ] as View[]
          ).map((item) => (
            <button
              key={item}
              className={`cursor-pointer border-0 px-[9px] py-[7px] font-mono text-[11px] capitalize transition-colors focus-visible:outline-2 focus-visible:outline-orange ${view === item ? "bg-ink text-paper" : "bg-transparent text-muted hover:bg-ink hover:text-paper"}`}
              onClick={() => setView(item)}
            >
              {item}
            </button>
          ))}
        </div>
        <div className="grid size-[30px] place-items-center bg-acid font-mono text-[11px] max-[850px]:hidden">
          {profile?.name.slice(0, 2).toUpperCase() ?? "CL"}
        </div>
      </nav>
      <header className="mx-auto mb-[34px] flex max-w-[1280px] flex-col items-start gap-6 min-[851px]:flex-row min-[851px]:items-end min-[851px]:justify-between">
        <div>
          <p className="mb-2.5 font-mono text-[11px] font-medium text-muted">
            COMMAND CENTER / {view.toUpperCase()}
          </p>
          <h1 className="m-0 max-w-[680px] text-[clamp(34px,5vw,68px)] leading-[.96] font-semibold">
            {view === "dashboard"
              ? "Make every solve count."
              : view === "cube"
                ? "The cube is your canvas."
                : view === "timer"
                  ? "Speed is a byproduct of clarity."
                  : view === "statistics"
                    ? "Progress, made visible."
                    : "Keep the hands moving."}
          </h1>
          <p className="mt-[18px] max-w-[510px] text-base leading-6 text-muted">
            A focused workspace for learning, solving, and building speed one
            deliberate turn at a time.
          </p>
        </div>
        <div className="inline-flex items-center gap-2 border border-line px-3.5 py-2.5 font-mono text-[11px] font-medium whitespace-nowrap text-muted min-[851px]:mb-0">
          <span className={`inline-block size-[7px] rounded-full ${apiLoading ? "bg-orange" : apiError ? "bg-[#c94b42]" : "bg-[#7dd39b]"}`} />
          {apiLoading ? "SYNCING" : apiError ? "OFFLINE" : "ONLINE"} / {message}
        </div>
      </header>
      {apiError && (
        <div className="mx-auto mb-5 flex max-w-[1280px] flex-wrap items-center justify-between gap-3 border-l-2 border-orange bg-white/70 px-4 py-3 text-sm" role="alert">
          <p className="m-0 text-ink">{apiError}</p>
          <ActionButton
            className="w-auto px-3 py-2"
            variant="secondary"
            onClick={() => setApiRetry((retry) => retry + 1)}
          >
            Retry connection
          </ActionButton>
        </div>
      )}
      <section className="mx-auto grid max-w-[1280px] grid-cols-1 gap-[18px] min-[851px]:grid-cols-[minmax(0,1.5fr)_minmax(300px,.8fr)]">
        <div className="border border-line bg-white/60 p-[18px]">
          <div className="flex items-start justify-between gap-3.5">
            <SectionLabel>LIVE CUBE / 01</SectionLabel>
            <ActionButton variant="quiet" onClick={reset}>
              Reset state
            </ActionButton>
          </div>
          <div className="mt-2 grid min-h-[420px] place-items-center bg-[#19231f] min-[851px]:min-h-[560px] [&>div]:h-full [&>div]:w-full">
            <CubePlayer
              state={state}
              solution={solution}
              autoPlay={false}
              onMove={applyMove}
              onFaceMove={applyMove}
            />
          </div>
          <div className="flex flex-wrap items-center gap-x-[22px] gap-y-2 pt-3.5 font-mono text-[11px] text-muted">
            <span>Front <b className="font-medium text-ink">Green</b></span>
            <span>Up <b className="font-medium text-ink">White</b></span>
            <span>Right <b className="font-medium text-ink">Red</b></span>
            <button
              className="cursor-pointer border-0 border-b border-ink bg-transparent text-[11px] text-ink hover:text-muted min-[851px]:ml-auto"
              onClick={() => setView("cube")}
            >
              Open 3D view ↗
            </button>
          </div>
        </div>
        <aside className="grid content-start gap-[18px] max-[850px]:[&>section]:mb-[18px]">
          <Panel>
            <div className="flex items-start justify-between gap-3.5">
              <SectionLabel>QUICK ACTIONS</SectionLabel>
              <span className="font-mono text-[10px] text-muted">{apiLoading ? "CONNECTING" : apiError ? "OFFLINE" : "API READY"}</span>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-[7px]">
              {([
                ["▣", "Scan cube", () => setView("scanner")],
                ["⌁", "Find solution", solve],
                ["◷", "Start timer", () => setView("timer")],
                ["◎", "Train today", () => setView("training")],
              ] as [string, string, () => void][]).map(([icon, label, action]) => (
                <button
                  key={label}
                  className="min-h-[76px] cursor-pointer border border-line bg-transparent p-3 text-left text-[21px] hover:bg-acid"
                  onClick={action}
                >
                  {icon}
                  <span className="mt-3 block font-mono text-[11px]">
                    {label}
                  </span>
                </button>
              ))}
            </div>
          </Panel>
          <Panel>
            <div className="flex items-start justify-between gap-3.5">
              <div>
                <SectionLabel>SESSION SNAPSHOT</SectionLabel>
                <h2 className="my-[18px] text-xl font-semibold">Today at a glance</h2>
              </div>
              <ActionButton
                variant="quiet"
                onClick={() => setView("statistics")}
              >
                Details
              </ActionButton>
            </div>
            <div className="grid grid-cols-3 gap-2.5">
              <div className="border-l-2 border-acid pl-2.5">
                <strong className="block text-[19px]">{records.length}</strong>
                <span className="block text-xs leading-[1.45] text-muted">solves</span>
              </div>
              <div className="border-l-2 border-acid pl-2.5">
                <strong className="block text-[19px]">{average(5)}</strong>
                <span className="block text-xs leading-[1.45] text-muted">Ao5</span>
              </div>
              <div className="border-l-2 border-acid pl-2.5">
                <strong className="block text-[19px]">
                  {statistics?.best_time_ms == null ? "--" : formatTime(statistics.best_time_ms)}
                </strong>
                <span className="block text-xs leading-[1.45] text-muted">best</span>
              </div>
            </div>
          </Panel>
          <Panel>
            <SectionLabel>NEXT REP</SectionLabel>
            <h2 className="my-[18px] text-xl font-semibold">R U R&apos; U&apos;</h2>
            <p className="text-xs leading-[1.45] text-muted">
              Four-move trigger · right-handed
            </p>
            <ActionButton
              onClick={() => {
                setSolution(["R", "U", "R'", "U'"]);
                setView("training");
              }}
            >
              Practice algorithm <span className="ml-auto">→</span>
            </ActionButton>
          </Panel>
        </aside>
      </section>
      <section className="mx-auto mt-[18px] grid max-w-[1280px] grid-cols-1 gap-[18px] min-[851px]:grid-cols-[1.2fr_.8fr]">
        <Panel className="p-5">
          <div className="flex items-start justify-between gap-3.5">
            <div>
              <SectionLabel>MANUAL INPUT</SectionLabel>
              <h2 className="my-[18px] text-xl font-semibold">Build a state</h2>
            </div>
            <span className="text-xs text-muted">Edit stickers</span>
          </div>
          <div className="flex flex-col items-start justify-between gap-3 min-[851px]:flex-row min-[851px]:items-center">
            <div className="flex gap-1">
              {FACE_NAMES.map((face) => (
                <button
                  key={face}
                  className={`cursor-pointer border border-line px-[9px] py-[7px] font-mono text-[11px] ${editFace === face ? "bg-ink text-white" : "bg-transparent text-ink hover:bg-white"}`}
                  onClick={() => setEditFace(face)}
                >
                  {face}
                </button>
              ))}
            </div>
            <div className="flex gap-1">
              {COLORS.map((color) => (
                <button
                  key={color}
                  className={`size-[22px] cursor-pointer rounded-full border-2 border-transparent ${editColor === color ? "outline-2 outline-acid" : ""}`}
                  style={{
                    background:
                      color === CubeColor.White
                        ? "#f5f4e9"
                        : color === CubeColor.Yellow
                          ? "#e8cc45"
                          : color === CubeColor.Red
                            ? "#c94b42"
                            : color === CubeColor.Orange
                              ? "#e27d45"
                              : color === CubeColor.Green
                                ? "#5b9a72"
                                : "#557ca5",
                  }}
                  aria-label={`Set ${COLOR_NAMES[color]}`}
                  onClick={() => setEditColor(color)}
                  aria-pressed={editColor === color}
                />
              ))}
            </div>
          </div>
          <div className="mt-[18px] grid grid-cols-[repeat(3,48px)] gap-[5px]">
            {state[editFace].map((color, index) => (
              <button
                key={index}
                className="aspect-square cursor-pointer border border-ink font-mono text-[10px] text-ink"
                style={{
                  background:
                    color === "W"
                      ? "#f5f4e9"
                      : color === "Y"
                        ? "#e8cc45"
                        : color === "R"
                          ? "#c94b42"
                          : color === "O"
                            ? "#e27d45"
                            : color === "G"
                              ? "#5b9a72"
                              : "#557ca5",
                }}
                onClick={() => editSticker(index, editColor)}
                aria-pressed={editColor === color}
                aria-label={`${editFace} sticker ${index + 1}: ${COLOR_NAMES[color]}`}
              >
                {index + 1}
              </button>
            ))}
          </div>
          <p className="mt-3 text-xs leading-[1.45] text-muted">
            Select a face, choose a color, then click a sticker position. The
            shared cube state updates immediately.
          </p>
        </Panel>
        <Panel>
          <div className="flex items-start justify-between gap-3.5">
            <div>
              <SectionLabel>RECENT SOLVES</SectionLabel>
              <h2 className="my-[18px] text-xl font-semibold">Session history</h2>
            </div>
            <ActionButton
              variant="quiet"
              onClick={() => setView("statistics")}
            >
              All stats
            </ActionButton>
          </div>
          {apiLoading ? (
            <p className="text-xs leading-[1.45] text-muted">Loading saved solves…</p>
          ) : records.length === 0 ? (
            <p className="text-xs leading-[1.45] text-muted">
              No solves yet. Start the timer to record your first attempt.
            </p>
          ) : (
            <div className="grid gap-px">
              {records.slice(0, 4).map((record, index) => (
                <div
                  className="grid grid-cols-[40px_1fr_auto] items-center border-b border-line py-[11px]"
                  key={record.id ?? `${record.created_at}-${index}`}
                >
                  <span className="font-mono text-[10px] text-muted">
                    #{String(index + 1).padStart(2, "0")}
                  </span>
                  <strong>
                    {record.is_dnf
                      ? "DNF"
                      : formatTime(record.time_ms + (record.penalty_ms ?? 0))}
                  </strong>
                  <small className="font-mono text-[10px] text-muted">
                    {record.created_at
                      ? new Date(record.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : ""}
                  </small>
                </div>
              ))}
            </div>
          )}
        </Panel>
      </section>
      {view === "timer" && (
        <section className="mx-auto mt-[18px] max-w-[1280px]">
          <Panel>
            <SectionLabel>SPEED TIMER</SectionLabel>
            <div className="my-[22px] font-mono text-[clamp(44px,8vw,100px)] font-semibold">
              {formatTime(elapsed)}
            </div>
            <p className="text-xs leading-[1.45] text-muted">
              Spacebar-ready session timer · {records.length} recorded solves
            </p>
            <label className="mb-4 flex max-w-56 flex-col gap-1 font-mono text-[11px] text-muted">
              Result penalty
              <select
                className="border border-line bg-white px-2 py-2 text-sm text-ink"
                value={solvePenalty}
                onChange={(event) =>
                  setSolvePenalty(event.target.value as typeof solvePenalty)
                }
              >
                <option value="none">None</option>
                <option value="plus2">+2 seconds</option>
                <option value="dnf">DNF</option>
              </select>
            </label>
            <ActionButton
              className="w-auto bg-orange px-6 py-3.5 text-ink hover:bg-[#ff885b]"
              onClick={toggleTimer}
            >
              {timerRunning ? "Stop and save" : "Start solve"}
            </ActionButton>
            <div className="mt-6 flex flex-wrap gap-7 font-mono text-[11px]">
              <span>Ao5 <b className="mt-1 block text-base">{average(5)}</b></span>
              <span>Ao12 <b className="mt-1 block text-base">{average(12)}</b></span>
              <span>Ao100 <b className="mt-1 block text-base">{average(100)}</b></span>
            </div>
            {apiError && <p className="mt-4 text-sm text-[#a33b31]" role="alert">{apiError}</p>}
          </Panel>
        </section>
      )}
      {view !== "dashboard" && view !== "timer" && (
        <section className="mx-auto mt-[18px] max-w-[1280px]">
          <Panel className="min-h-[210px]">
            {view === "scanner" && (
              <>
                <SectionLabel>SCANNER</SectionLabel>
                <h2 className="my-[18px] text-xl font-semibold">Bring a cube into the lab</h2>
                <p className="text-xs leading-[1.45] text-muted">
                  {scanFiles.length} face images selected
                </p>
                <div className="mt-[22px] flex flex-wrap items-center gap-3">
                  <label className="cursor-pointer border border-ink px-4 py-3 text-sm hover:bg-white">
                    Choose face photos
                    <input
                      className="sr-only"
                      type="file"
                      accept="image/png,image/jpeg,image/webp"
                      multiple
                      onChange={(event) => {
                        setScanFiles(Array.from(event.currentTarget.files ?? []));
                        setApiError(null);
                      }}
                    />
                  </label>
                  <ActionButton
                    className="w-auto"
                    disabled={scanLoading || scanFiles.length === 0}
                    onClick={scanAndSolve}
                  >
                    {scanLoading ? "Scanning and solving…" : "Scan and solve"}
                  </ActionButton>
                  <ActionButton
                    className="w-auto"
                    variant="secondary"
                    disabled={cameraActive || scanLoading}
                    onClick={() => {
                      setApiError(null);
                      setCameraActive(true);
                    }}
                  >
                    Start live camera
                  </ActionButton>
                </div>
                {cameraActive && (
                  <div className="mt-5 grid gap-3 border-t border-line pt-5 sm:grid-cols-[minmax(0,1fr)_auto]">
                    <div>
                      <video
                        ref={videoRef}
                        className="max-h-[360px] w-full bg-[#19231f] object-contain"
                        autoPlay
                        muted
                        playsInline
                        aria-label="Live cube camera"
                      />
                      <canvas ref={canvasRef} className="hidden" />
                    </div>
                    <div className="min-w-48">
                      <SectionLabel>LIVE SCAN</SectionLabel>
                      <p className="mt-2 text-sm">
                        {scanSession.connected ? "Connected" : "Connecting…"}
                        {` · ${scanSession.facesDetected}/6 faces`}
                      </p>
                      <p className="text-xs text-muted">
                        {scanSession.requestedFace
                          ? `Show face ${scanSession.requestedFace} to the camera`
                          : "Hold a face steady in view, then rotate when asked."}
                      </p>
                      {scanSession.framesProcessed > 0 && (
                        <p className="font-mono text-xs text-muted">
                          {Math.round(scanSession.confidence * 100)}% confidence · {scanSession.framesProcessed} frames
                        </p>
                      )}
                      {scanSession.error && (
                        <p className="text-sm text-[#a33b31]" role="status">
                          {scanSession.error}
                        </p>
                      )}
                      <div className="mt-3 flex flex-wrap gap-2">
                        <ActionButton
                          className="w-auto px-3 py-2"
                          variant="secondary"
                          disabled={!scanSession.connected || !scanSession.requestedFace}
                          onClick={() => scanSession.retry(scanSession.requestedFace ?? "U")}
                        >
                          Retry face
                        </ActionButton>
                        <ActionButton
                          className="w-auto bg-orange px-3 py-2 text-ink"
                          onClick={() => {
                            scanSession.cancel();
                            setCameraActive(false);
                          }}
                        >
                          Cancel scan
                        </ActionButton>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
            {view === "solver" && (
              <>
                <SectionLabel>SOLVER</SectionLabel>
                <h2 className="my-[18px] text-xl font-semibold">Solution interface</h2>
                <p className="text-xs leading-[1.45] text-muted">
                  {solveLoading
                    ? "Validating the current state and asking the solver…"
                    : solution.length
                      ? `The API returned a verified ${solution.length}-move solution.`
                      : "The API confirmed the cube is solved."}
                </p>
                <div className="my-6 border-l-[3px] border-acid bg-white p-[18px] font-mono text-[15px] leading-[1.8]">
                  {solution.length ? solution.join("  ") : "SOLVED"}
                </div>
                <ActionButton onClick={() => setView("cube")}>
                  Visualize solution <span>→</span>
                </ActionButton>
              </>
            )}
            {view === "cube" && (
              <>
                <SectionLabel>3D CUBE</SectionLabel>
                <h2 className="my-[18px] text-xl font-semibold">Interactive model</h2>
                <p className="text-xs leading-[1.45] text-muted">
                  Orbit the model, click a visible face, or use the manual deck
                  to apply moves through cube-core.
                </p>
                <ActionButton onClick={() => setView("dashboard")}>
                  Return to workspace <span>→</span>
                </ActionButton>
              </>
            )}
            {view === "training" && (
              <>
                <SectionLabel>TRAINING</SectionLabel>
                <h2 className="my-[18px] text-xl font-semibold">Today&apos;s focused set</h2>
                <p className="mb-4 text-xs text-muted">
                  {trainingAttempts.length} saved attempts
                  {trainingAttempts.length
                    ? ` · latest recognition ${formatTime(trainingAttempts[0].recognition_time_ms)}`
                    : " · no attempts yet"}
                </p>
                <div className="grid items-center gap-4 border-t border-line py-4 min-[851px]:grid-cols-[1fr_1fr_auto]">
                  <strong>R U R&apos; U&apos;</strong>
                  <span>Trigger recognition</span>
                  <ActionButton
                    className="min-[851px]:w-auto"
                    onClick={() => setSolution(["R", "U", "R'", "U'"])}
                  >
                    Load drill <span>→</span>
                  </ActionButton>
                </div>
                <div className="grid items-center gap-4 border-t border-line py-4 min-[851px]:grid-cols-[1fr_1fr_auto]">
                  <strong>Accuracy first</strong>
                  <span>Repeat 5 clean reps</span>
                  <ActionButton
                    className="min-[851px]:w-auto"
                    variant="secondary"
                    disabled={trainingSaving}
                    onClick={() => {
                      if (trainingStartedAt === null) {
                        setTrainingStartedAt(Date.now());
                        setTrainingRecognitionMs(null);
                        setMessage("Recognition timer started");
                      } else if (trainingRecognitionMs === null) {
                        setTrainingRecognitionMs(Date.now() - trainingStartedAt);
                        setMessage("Recognition recorded · complete the rep");
                      } else {
                        void finishTrainingAttempt();
                      }
                    }}
                  >
                    {trainingSaving
                      ? "Saving…"
                      : trainingStartedAt === null
                        ? "Start recognition"
                        : trainingRecognitionMs === null
                          ? "Recognized"
                          : "Complete rep"}
                  </ActionButton>
                </div>
              </>
            )}
            {view === "coaching" && (
              <>
                <SectionLabel>COACHING</SectionLabel>
                <h2 className="my-[18px] text-xl font-semibold">Understand this cube state</h2>
                <div className="flex flex-wrap items-end gap-3">
                  <label className="flex flex-col gap-1 font-mono text-[11px] text-muted">
                    Focus
                    <select
                      className="border border-line bg-white px-3 py-2 text-sm text-ink"
                      value={coachingFocus}
                      onChange={(event) => setCoachingFocus(event.target.value as typeof coachingFocus)}
                    >
                      <option value="overall">Overall</option>
                      <option value="cross">Cross</option>
                      <option value="f2l">F2L</option>
                      <option value="oll">OLL</option>
                      <option value="pll">PLL</option>
                    </select>
                  </label>
                  <ActionButton className="w-auto" disabled={coachingLoading} onClick={requestCoaching}>
                    {coachingLoading ? "Analyzing…" : "Get coaching"}
                  </ActionButton>
                </div>
                {coachingResult && (
                  <div className="mt-5 border-t border-line pt-4">
                    <p className="text-sm leading-6">{coachingResult.explanation}</p>
                    <ul className="mt-3 list-disc space-y-2 pl-5 text-sm">
                      {coachingResult.key_points.map((point) => <li key={point}>{point}</li>)}
                    </ul>
                    <p className="mt-4 font-mono text-xs text-muted">
                      {coachingResult.difficulty_level} · {coachingResult.suggested_algorithms.join("  ·  ")}
                    </p>
                  </div>
                )}
              </>
            )}
            {view === "statistics" && (
              <>
                <SectionLabel>STATISTICS</SectionLabel>
                <h2 className="my-[18px] text-xl font-semibold">Saved profile performance</h2>
                <div className="my-7 flex flex-wrap gap-[42px]">
                  <div><strong className="block font-mono text-[26px]">{statistics?.total_solves ?? "--"}</strong><span className="mt-1.5 block text-xs text-muted">total solves</span></div>
                  <div><strong className="block font-mono text-[26px]">{average(5)}</strong><span className="mt-1.5 block text-xs text-muted">rolling Ao5</span></div>
                  <div><strong className="block font-mono text-[26px]">{statistics?.best_time_ms == null ? "--" : formatTime(statistics.best_time_ms)}</strong><span className="mt-1.5 block text-xs text-muted">personal best</span></div>
                </div>
                <div className="flex h-[130px] items-end gap-[18px] border-b border-line px-3">
                  {records.slice(0, 7).reverse().map((record) => (
                    <div className="grid h-full flex-1 items-end gap-[7px] text-center" key={record.id}>
                      <i className="block min-h-[15px] bg-orange" style={{ height: `${Math.max(15, (record.time_ms / Math.max(statistics?.worst_time_ms ?? record.time_ms, 1)) * 100)}%` }} />
                      <small className="font-mono text-[10px] text-muted">{record.created_at ? new Date(record.created_at).toLocaleDateString([], { weekday: "short" }) : "Solve"}</small>
                    </div>
                  ))}
                </div>
              </>
            )}
            {view === "profile" && (
              <>
                <SectionLabel>PROFILE</SectionLabel>
                <h2 className="my-[18px] text-xl font-semibold">{profile?.name ?? "Cube Lab profile"}</h2>
                <p className="text-xs leading-[1.45] text-muted">
                  Beginner track · learning consistency over speed.
                </p>
                <div className="grid grid-cols-[1fr_auto] items-center gap-4 border-t border-line py-4 text-xs">
                  <span className="text-muted">Current focus</span>
                  <strong>Layer-by-layer</strong>
                </div>
                <div className="grid grid-cols-[1fr_auto] items-center gap-4 border-t border-line py-4 text-xs">
                  <span className="text-muted">Practice streak</span>
                  <strong>{statistics?.total_solves ? `${statistics.total_solves} solves` : "Start today"}</strong>
                </div>
                <p className="text-xs text-muted">Your solve history and statistics are loaded from the API profile.</p>
              </>
            )}
          </Panel>
        </section>
      )}
    </main>
  );
}
