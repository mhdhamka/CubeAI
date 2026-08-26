import { useEffect, useState } from "react";
import type { CubeState } from "../cube-core/CubeState";
import type { Move } from "../cube-core/Move";
import { Cube3D } from "./Cube3D";
import type { Cube3DProps } from "./Cube3D";

export interface CubePlayerProps extends Omit<Cube3DProps, "animationMove" | "animationProgress"> {
  solution: Move[];
  moveDuration?: number | undefined;
  autoPlay?: boolean | undefined;
  onMove?: ((move: Move, index: number) => void) | undefined;
}

export function CubePlayer({
  solution,
  moveDuration = 650,
  autoPlay = false,
  onMove,
  state,
  ...cubeProps
}: CubePlayerProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [playing, setPlaying] = useState(autoPlay);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    setCurrentIndex(0);
    setProgress(0);
    setPlaying(autoPlay);
  }, [solution, autoPlay]);

  useEffect(() => {
    if (!playing || currentIndex >= solution.length) {
      if (currentIndex >= solution.length) setPlaying(false);
      return;
    }

    const started = performance.now();
    const timer = window.setInterval(() => {
      const elapsed = performance.now() - started;
      const nextProgress = Math.min(elapsed / moveDuration, 1);
      setProgress(nextProgress);
      if (nextProgress >= 1) {
        const move = solution[currentIndex];
        if (move) onMove?.(move, currentIndex);
        setCurrentIndex((index) => index + 1);
        setProgress(0);
      }
    }, 16);

    return () => window.clearInterval(timer);
  }, [currentIndex, moveDuration, onMove, playing, solution]);

  const togglePlaying = () => {
    if (currentIndex >= solution.length) {
      setCurrentIndex(0);
      setProgress(0);
    }
    setPlaying((value) => !value);
  };

  const reset = () => {
    setPlaying(false);
    setCurrentIndex(0);
    setProgress(0);
  };

  return (
    <div style={{ display: "grid", gridTemplateRows: "minmax(320px, 1fr) auto", height: "100%", minHeight: 380 }}>
      <Cube3D
        {...cubeProps}
        state={state}
        animationMove={solution[currentIndex]}
        animationProgress={progress}
      />
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, padding: "12px 4px" }}>
        <span aria-live="polite">
          {solution.length === 0 ? "Solved" : `${Math.min(currentIndex + (progress > 0 ? 1 : 0), solution.length)} / ${solution.length}`}
        </span>
        <div style={{ display: "flex", gap: 8 }}>
          <button type="button" onClick={togglePlaying} aria-label={playing ? "Pause solution" : "Play solution"}>
            {playing ? "Pause" : "Play"}
          </button>
          <button type="button" onClick={reset} aria-label="Reset solution playback">
            Reset
          </button>
        </div>
      </div>
    </div>
  );
}
