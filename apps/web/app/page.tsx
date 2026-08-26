"use client";

import { useMemo, useState } from "react";
import { Cube } from "../../../packages/cube-core/Cube";
import type { Move } from "../../../packages/cube-core/Move";
import { CubePlayer } from "../../../packages/cube-renderer/CubePlayer";
import { CubeRenderer } from "../../../packages/cube-renderer/CubeRenderer";
import type { CubeState } from "../../../packages/cube-core/CubeState";
import styles from "./page.module.css";

const SOLUTION: Move[] = ["R", "U", "R'", "U'", "F2", "L", "D"];
const FACES: Move[] = ["U", "R", "F", "D", "L", "B"];

export default function Home() {
  const [state, setState] = useState<CubeState>(() => new Cube().getState());
  const [solution, setSolution] = useState<Move[]>(SOLUTION);
  const [selectedMove, setSelectedMove] = useState<Move>("R");
  const [message, setMessage] = useState("Ready to explore");

  const svgPreview = useMemo(() => new CubeRenderer({ size: 120 }).render(state), [state]);

  const applyMove = (move: Move) => {
    const next = new Cube(state);
    next.move(move);
    setState(next.getState());
    setMessage(`${move} applied`);
  };

  const scramble = () => {
    const next = new Cube();
    const moves: Move[] = ["R", "U", "F", "L'", "D2", "B", "R2"];
    next.applyMoves(moves);
    setState(next.getState());
    setMessage("Scrambled cube loaded");
  };

  const reset = () => {
    setState(new Cube().getState());
    setMessage("Cube reset");
  };

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <p className={styles.eyebrow}>CUBE / LAB 03</p>
          <h1 className={styles.title}>Turn theory into muscle memory.</h1>
          <p className={styles.subtitle}>A tactile 3D workspace for learning, replaying, and understanding every move.</p>
        </div>
        <div className={styles.status}><span /> {message}</div>
      </header>

      <section className={styles.workspace}>
        <div className={styles.stage}>
          <div className={styles.stageTop}><span>LIVE MODEL</span><span>Orbit to inspect</span></div>
          <div className={styles.model}><CubePlayer state={state} solution={solution} autoPlay={false} onMove={(move) => applyMove(move)} onFaceMove={(face) => applyMove(face)} /></div>
          <div className={styles.stageBottom}><span>Front: Green</span><span>Up: White</span><span>Right: Red</span></div>
        </div>

        <aside className={styles.panel}>
          <div className={styles.panelHeading}><div><p className={styles.eyebrow}>MOVE DECK</p><h2>Manual practice</h2></div><button className={styles.textButton} onClick={reset}>Reset</button></div>
          <div className={styles.moveGrid}>
            {FACES.map((face) => <button key={face} className={selectedMove[0] === face ? styles.moveActive : styles.move} onClick={() => { setSelectedMove(face); applyMove(face); }}>{face}</button>)}
          </div>
          <div className={styles.modifiers}>
            {["", "'", "2"].map((modifier) => { const move = `${selectedMove[0]}${modifier}` as Move; return <button key={modifier || "cw"} className={styles.modifier} onClick={() => applyMove(move)}>{modifier || "CW"}</button>; })}
          </div>
          <button className={styles.scramble} onClick={scramble}>Load practice scramble <span>↗</span></button>

          <div className={styles.divider} />
          <div className={styles.panelHeading}><div><p className={styles.eyebrow}>ALGORITHM VISUALIZER</p><h2>Playback sequence</h2></div><span className={styles.count}>{solution.length} moves</span></div>
          <div className={styles.sequence}>{solution.map((move, index) => <button key={`${move}-${index}`} className={styles.sequenceMove} onClick={() => applyMove(move)}><small>{String(index + 1).padStart(2, "0")}</small>{move}</button>)}</div>
          <div className={styles.solutionEdit}><input aria-label="Algorithm" value={solution.join(" ")} onChange={(event) => setSolution(event.target.value.split(/\s+/).filter(Boolean) as Move[])} /><span>↵</span></div>
          <p className={styles.hint}>Choose a face to rotate it. Use the player below the model to replay the sequence.</p>
        </aside>
      </section>

      <section className={styles.footerGrid}>
        <div><p className={styles.eyebrow}>CURRENT STATE</p><strong>{state.U[4] === "W" ? "Solved reference" : "Practice state"}</strong><p>All changes are driven by the shared cube-core engine.</p></div>
        <div className={styles.miniPreview} dangerouslySetInnerHTML={{ __html: svgPreview }} />
      </section>
    </main>
  );
}
