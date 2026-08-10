import {
  CubeState,
} from "./CubeState";

import {
  createSolvedState,
  rotateFaceClockwise,
} from "./Face";

import { Move } from "./Move";

export class Cube {
  private state: CubeState;

  constructor(state?: CubeState) {
    this.state = state ?? createSolvedState();
  }

  public getState(): CubeState {
    return structuredClone(this.state);
  }

  public reset(): void {
    this.state = createSolvedState();
  }

  public isSolved(): boolean {
    return Object.values(this.state).every((face) =>
      face.every((color) => color === face[4])
    );
  }

  public move(move: Move): void {
    const face = move[0];
    const modifier = move.slice(1);

    const times =
      modifier === "2"
        ? 2
        : modifier === "'"
          ? 3
          : 1;

    for (let i = 0; i < times; i++) {
      this.rotate(face);
    }
  }

  public applyMoves(moves: Move[]): void {
    for (const move of moves) {
      this.move(move);
    }
  }

  private rotate(face: string): void {
    switch (face) {
      case "U":
        this.rotateU();
        break;

      case "D":
        this.rotateD();
        break;

      case "R":
        this.rotateR();
        break;

      case "L":
        this.rotateL();
        break;

      case "F":
        this.rotateF();
        break;

      case "B":
        this.rotateB();
        break;

      default:
        throw new Error(`Unsupported move: ${face}`);
    }
  }

  /*
   * ---------------------------------------------------------
   * U
   * ---------------------------------------------------------
   */

  private rotateU(): void {
    this.state.U = rotateFaceClockwise(this.state.U);

    const F = [...this.state.F];
    const R = [...this.state.R];
    const B = [...this.state.B];
    const L = [...this.state.L];

    /*
     * U clockwise:
     *
     * F -> L
     * L -> B
     * B -> R
     * R -> F
     */

    for (let i = 0; i < 3; i++) {
      this.state.R[i] = B[i];
      this.state.F[i] = R[i];
      this.state.L[i] = F[i];
      this.state.B[i] = L[i];
    }
  }

  /*
   * ---------------------------------------------------------
   * D
   * ---------------------------------------------------------
   */

  private rotateD(): void {
    this.state.D = rotateFaceClockwise(this.state.D);

    const F = [...this.state.F];
    const R = [...this.state.R];
    const B = [...this.state.B];
    const L = [...this.state.L];

    /*
     * D clockwise:
     *
     * F -> R
     * R -> B
     * B -> L
     * L -> F
     */

    for (let i = 0; i < 3; i++) {
      this.state.R[6 + i] = F[6 + i];
      this.state.B[6 + i] = R[6 + i];
      this.state.L[6 + i] = B[6 + i];
      this.state.F[6 + i] = L[6 + i];
    }
  }

  /*
   * ---------------------------------------------------------
   * R
   * ---------------------------------------------------------
   */

  private rotateR(): void {
    this.state.R = rotateFaceClockwise(this.state.R);

    const U = [...this.state.U];
    const F = [...this.state.F];
    const D = [...this.state.D];
    const B = [...this.state.B];

    /*
     * R clockwise:
     *
     * F right -> U right
     * D right -> F right
     * B left  -> D right
     * U right -> B left
     */

      // B left column -> U right column
      this.state.U[2] = B[6];
      this.state.U[5] = B[3];
      this.state.U[8] = B[0];

      // U right column -> F right column
      this.state.F[2] = U[2];
      this.state.F[5] = U[5];
      this.state.F[8] = U[8];

      // F right column -> D right column
      this.state.D[2] = F[2];
      this.state.D[5] = F[5];
      this.state.D[8] = F[8];

      // D right column -> B left column
      this.state.B[6] = D[8];
      this.state.B[3] = D[5];
      this.state.B[0] = D[2];
  }

  /*
   * ---------------------------------------------------------
   * L
   * ---------------------------------------------------------
   */

  private rotateL(): void {
    this.state.L = rotateFaceClockwise(this.state.L);

    const U = [...this.state.U];
    const F = [...this.state.F];
    const D = [...this.state.D];
    const B = [...this.state.B];

    /*
     * L clockwise:
     *
     * F left -> U left
     * D left -> F left
     * B right -> D left
     * U left -> B right
     */

    this.state.U[0] = F[0];
    this.state.U[3] = F[3];
    this.state.U[6] = F[6];

    this.state.F[0] = D[0];
    this.state.F[3] = D[3];
    this.state.F[6] = D[6];

    this.state.D[0] = B[8];
    this.state.D[3] = B[5];
    this.state.D[6] = B[2];

    this.state.B[2] = U[6];
    this.state.B[5] = U[3];
    this.state.B[8] = U[0];
  }

  /*
   * ---------------------------------------------------------
   * F
   * ---------------------------------------------------------
   */

  private rotateF(): void {
    this.state.F = rotateFaceClockwise(this.state.F);

    const U = [...this.state.U];
    const R = [...this.state.R];
    const D = [...this.state.D];
    const L = [...this.state.L];

    /*
     * F clockwise:
     *
     * L right -> U bottom
     * U bottom -> R left
     * R left -> D top
     * D top -> L right
     */

    this.state.U[6] = L[8];
    this.state.U[7] = L[5];
    this.state.U[8] = L[2];

    this.state.R[0] = U[6];
    this.state.R[3] = U[7];
    this.state.R[6] = U[8];

    this.state.D[0] = R[6];
    this.state.D[1] = R[3];
    this.state.D[2] = R[0];

    this.state.L[2] = D[0];
    this.state.L[5] = D[1];
    this.state.L[8] = D[2];
  }

  /*
   * ---------------------------------------------------------
   * B
   * ---------------------------------------------------------
   */

  private rotateB(): void {
    this.state.B = rotateFaceClockwise(this.state.B);

    const U = [...this.state.U];
    const R = [...this.state.R];
    const D = [...this.state.D];
    const L = [...this.state.L];

    /*
     * B clockwise:
     *
     * L left -> U top
     * U top -> R right
     * R right -> D bottom
     * D bottom -> L left
     */

    this.state.U[0] = L[6];
    this.state.U[1] = L[3];
    this.state.U[2] = L[0];

    this.state.R[2] = U[0];
    this.state.R[5] = U[1];
    this.state.R[8] = U[2];

    this.state.D[6] = R[8];
    this.state.D[7] = R[5];
    this.state.D[8] = R[2];

    this.state.L[0] = D[6];
    this.state.L[3] = D[7];
    this.state.L[6] = D[8];
  }
}