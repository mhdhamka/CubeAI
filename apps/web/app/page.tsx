"use client";

import { useEffect, useMemo, useState } from "react";
import { Cube } from "../../../packages/cube-core/Cube";
import type { Move } from "../../../packages/cube-core/Move";
import { CubePlayer } from "../../../packages/cube-renderer/CubePlayer";
import { CubeRenderer } from "../../../packages/cube-renderer/CubeRenderer";
import { CubeColor } from "../../../packages/cube-core/CubeState";
import type { CubeState } from "../../../packages/cube-core/CubeState";
import styles from "./page.module.css";

const SOLUTION: Move[] = ["R", "U", "R'", "U'", "F2", "L", "D"];
const FACES: Move[] = ["U", "R", "F", "D", "L", "B"];
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
const INVERSE: Record<string, Move> = {
  U: "U'",
  "U'": "U",
  U2: "U2",
  R: "R'",
  "R'": "R",
  R2: "R2",
  F: "F'",
  "F'": "F",
  F2: "F2",
  D: "D'",
  "D'": "D",
  D2: "D2",
  L: "L'",
  "L'": "L",
  L2: "L2",
  B: "B'",
  "B'": "B",
  B2: "B2",
};
type View =
  | "dashboard"
  | "scanner"
  | "solver"
  | "cube"
  | "timer"
  | "training"
  | "statistics"
  | "profile";
type SolveRecord = { time: number; scramble: string; date: string };

export default function Home() {
  const [state, setState] = useState<CubeState>(() => new Cube().getState());
  const [solution, setSolution] = useState<Move[]>(SOLUTION);
  const [selectedMove, setSelectedMove] = useState<Move>("R");
  const [message, setMessage] = useState("Ready to explore");
  const [view, setView] = useState<View>("dashboard");
  const [moveHistory, setMoveHistory] = useState<Move[]>([]);
  const [editFace, setEditFace] = useState<keyof CubeState>("U");
  const [editColor, setEditColor] = useState<CubeColor>(CubeColor.White);
  const [timerRunning, setTimerRunning] = useState(false);
  const [timerStarted, setTimerStarted] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [records, setRecords] = useState<SolveRecord[]>([]);

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

  const svgPreview = useMemo(
    () => new CubeRenderer({ size: 120 }).render(state),
    [state],
  );

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

  const solve = () => {
    const nextSolution = [...moveHistory]
      .reverse()
      .map((move) => INVERSE[move])
      .filter((move): move is Move => move !== undefined);
    setSolution(nextSolution);
    setMessage(
      nextSolution.length
        ? "Solution generated from move history"
        : "Cube is already solved",
    );
    setView("solver");
  };

  const toggleTimer = () => {
    if (timerRunning) {
      const time = Date.now() - timerStarted;
      setElapsed(time);
      setTimerRunning(false);
      setRecords((current) =>
        [
          {
            time,
            scramble: moveHistory.join(" ") || "Solved",
            date: new Date().toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            }),
          },
          ...current,
        ].slice(0, 100),
      );
    } else {
      setElapsed(0);
      setTimerStarted(Date.now());
      setTimerRunning(true);
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
  const average = (count: number) =>
    records.length < count
      ? "--"
      : formatTime(
          records
            .slice(0, count)
            .reduce((sum, record) => sum + record.time, 0) / count,
        );

  return (
    <main className={styles.page}>
      <nav className={styles.nav}>
        <div className={styles.brand}>
          <span className={styles.brandMark}>✦</span>
          <strong>CUBE / LAB</strong>
          <small>practice OS</small>
        </div>
        <div className={styles.navLinks}>
          {(
            [
              "dashboard",
              "scanner",
              "solver",
              "cube",
              "timer",
              "training",
              "statistics",
              "profile",
            ] as View[]
          ).map((item) => (
            <button
              key={item}
              className={view === item ? styles.navActive : styles.navButton}
              onClick={() => setView(item)}
            >
              {item}
            </button>
          ))}
        </div>
        <div className={styles.avatar}>AM</div>
      </nav>
      <header className={styles.header}>
        <div>
          <p className={styles.eyebrow}>
            COMMAND CENTER / {view.toUpperCase()}
          </p>
          <h1 className={styles.title}>
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
          <p className={styles.subtitle}>
            A focused workspace for learning, solving, and building speed one
            deliberate turn at a time.
          </p>
        </div>
        <div className={styles.status}>
          <span /> {message}
        </div>
      </header>
      <section className={styles.dashboardGrid}>
        <div className={styles.mainCard}>
          <div className={styles.cardTop}>
            <span className={styles.kicker}>LIVE CUBE / 01</span>
            <button className={styles.textButton} onClick={reset}>
              Reset state
            </button>
          </div>
          <div className={styles.model}>
            <CubePlayer
              state={state}
              solution={solution}
              autoPlay={false}
              onMove={applyMove}
              onFaceMove={applyMove}
            />
          </div>
          <div className={styles.modelFooter}>
            <span>
              Front <b>Green</b>
            </span>
            <span>
              Up <b>White</b>
            </span>
            <span>
              Right <b>Red</b>
            </span>
            <button onClick={() => setView("cube")}>Open 3D view ↗</button>
          </div>
        </div>
        <aside className={styles.sideStack}>
          <section className={styles.card}>
            <div className={styles.cardTop}>
              <span className={styles.kicker}>QUICK ACTIONS</span>
              <span className={styles.liveDot}>ONLINE</span>
            </div>
            <div className={styles.quickGrid}>
              <button onClick={() => setView("scanner")}>
                ▣<span>Scan cube</span>
              </button>
              <button onClick={solve}>
                ⌁<span>Find solution</span>
              </button>
              <button onClick={() => setView("timer")}>
                ◷<span>Start timer</span>
              </button>
              <button onClick={() => setView("training")}>
                ◎<span>Train today</span>
              </button>
            </div>
          </section>
          <section className={styles.card}>
            <div className={styles.cardTop}>
              <div>
                <span className={styles.kicker}>SESSION SNAPSHOT</span>
                <h2>Today at a glance</h2>
              </div>
              <button
                className={styles.textButton}
                onClick={() => setView("statistics")}
              >
                Details
              </button>
            </div>
            <div className={styles.metrics}>
              <div>
                <strong>{records.length}</strong>
                <span>solves</span>
              </div>
              <div>
                <strong>{average(5)}</strong>
                <span>Ao5</span>
              </div>
              <div>
                <strong>
                  {records.length
                    ? formatTime(
                        Math.min(...records.map((record) => record.time)),
                      )
                    : "--"}
                </strong>
                <span>best</span>
              </div>
            </div>
          </section>
          <section className={styles.card}>
            <span className={styles.kicker}>NEXT REP</span>
            <h2>R U R' U'</h2>
            <p className={styles.muted}>Four-move trigger · right-handed</p>
            <button
              className={styles.primaryButton}
              onClick={() => {
                setSolution(["R", "U", "R'", "U'"]);
                setView("training");
              }}
            >
              Practice algorithm <span>→</span>
            </button>
          </section>
        </aside>
      </section>
      <section className={styles.lowerGrid}>
        <section className={styles.card}>
          <div className={styles.cardTop}>
            <div>
              <span className={styles.kicker}>MANUAL INPUT</span>
              <h2>Build a state</h2>
            </div>
            <span className={styles.muted}>Edit stickers</span>
          </div>
          <div className={styles.editorRow}>
            <div className={styles.faceTabs}>
              {FACE_NAMES.map((face) => (
                <button
                  key={face}
                  className={
                    editFace === face ? styles.faceActive : styles.faceTab
                  }
                  onClick={() => setEditFace(face)}
                >
                  {face}
                </button>
              ))}
            </div>
            <div className={styles.palette}>
              {COLORS.map((color) => (
                <button
                  key={color}
                  className={styles.swatch}
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
          <div className={styles.stickerEditor}>
            {state[editFace].map((color, index) => (
                <button
                key={index}
                className={styles.stickerCell}
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
              >
                {index + 1}
              </button>
            ))}
          </div>
          <p className={styles.hint}>
            Select a face, choose a color, then click a sticker position. The
            shared cube state updates immediately.
          </p>
        </section>
        <section className={styles.card}>
          <div className={styles.cardTop}>
            <div>
              <span className={styles.kicker}>RECENT SOLVES</span>
              <h2>Session history</h2>
            </div>
            <button
              className={styles.textButton}
              onClick={() => setView("statistics")}
            >
              All stats
            </button>
          </div>
          {records.length === 0 ? (
            <p className={styles.muted}>
              No solves yet. Start the timer to record your first attempt.
            </p>
          ) : (
            <div className={styles.history}>
              {records.slice(0, 4).map((record, index) => (
                <div key={`${record.date}-${index}`}>
                  <span>#{String(index + 1).padStart(2, "0")}</span>
                  <strong>{formatTime(record.time)}</strong>
                  <small>{record.date}</small>
                </div>
              ))}
            </div>
          )}
        </section>
      </section>
      {view === "timer" && (
        <section className={styles.timerOverlay}>
          <div className={styles.card}>
            <span className={styles.kicker}>SPEED TIMER</span>
            <div className={styles.timerValue}>{formatTime(elapsed)}</div>
            <p className={styles.muted}>
              Spacebar-ready session timer · {records.length} recorded solves
            </p>
            <button className={styles.timerButton} onClick={toggleTimer}>
              {timerRunning ? "Stop and save" : "Start solve"}
            </button>
            <div className={styles.averages}>
              <span>
                Ao5 <b>{average(5)}</b>
              </span>
              <span>
                Ao12 <b>{average(12)}</b>
              </span>
              <span>
                Ao100 <b>{average(100)}</b>
              </span>
            </div>
          </div>
        </section>
      )}
      {view !== "dashboard" && view !== "timer" && (
        <section className={styles.utilityOverlay}>
          <div className={styles.card}>
            {view === "scanner" && <><span className={styles.kicker}>SCANNER</span><h2>Bring a cube into the lab</h2><p className={styles.muted}>The vision pipeline accepts six face images or a live camera session. Use the Python scanner to produce a validated CubeState.</p><div className={styles.scannerActions}><button className={styles.primaryButton} onClick={() => setMessage("Run: py ai\\vision\\scanSession.py --camera")}>Open camera workflow <span>↗</span></button><button className={styles.secondaryButton} onClick={() => setMessage("Six face images ready to import")}>Import six face images</button></div></>}
            {view === "solver" && <><span className={styles.kicker}>SOLVER</span><h2>Solution interface</h2><p className={styles.muted}>{solution.length ? `A ${solution.length}-move inverse solution is ready from the current move history.` : "The current cube is solved."}</p><div className={styles.solutionLarge}>{solution.length ? solution.join("  ") : "SOLVED"}</div><button className={styles.primaryButton} onClick={() => setView("cube")}>Visualize solution <span>→</span></button></>}
            {view === "cube" && <><span className={styles.kicker}>3D CUBE</span><h2>Interactive model</h2><p className={styles.muted}>Orbit the model, click a visible face, or use the manual deck to apply moves through cube-core.</p><button className={styles.primaryButton} onClick={() => setView("dashboard")}>Return to workspace <span>→</span></button></>}
            {view === "training" && <><span className={styles.kicker}>TRAINING</span><h2>Today&apos;s focused set</h2><div className={styles.trainingRow}><strong>R U R&apos; U&apos;</strong><span>Trigger recognition</span><button className={styles.primaryButton} onClick={() => setSolution(["R", "U", "R'", "U'"])}>Load drill <span>→</span></button></div><div className={styles.trainingRow}><strong>Accuracy first</strong><span>Repeat 5 clean reps</span><button className={styles.secondaryButton} onClick={() => setMessage("Training goal started")}>Start goal</button></div></>}
            {view === "statistics" && <><span className={styles.kicker}>STATISTICS</span><h2>Session performance</h2><div className={styles.bigStats}><div><strong>{records.length}</strong><span>total solves</span></div><div><strong>{average(5)}</strong><span>rolling Ao5</span></div><div><strong>{records.length ? formatTime(Math.min(...records.map((record) => record.time))) : "--"}</strong><span>personal best</span></div></div><div className={styles.bars}>{["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day, index) => <div key={day}><i style={{ height: `${20 + ((records.length + index * 13) % 75)}%` }} /><small>{day}</small></div>)}</div></>}
            {view === "profile" && <><span className={styles.kicker}>PROFILE</span><h2>Alex Morgan</h2><p className={styles.muted}>Beginner track · learning consistency over speed.</p><div className={styles.profileLine}><span>Current focus</span><strong>Layer-by-layer</strong></div><div className={styles.profileLine}><span>Practice streak</span><strong>{records.length ? `${records.length} solves` : "Start today"}</strong></div><button className={styles.secondaryButton} onClick={() => setMessage("Profile settings are saved locally")}>Save profile settings</button></>}
          </div>
        </section>
      )}
    </main>
  );
}
