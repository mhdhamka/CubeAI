import {
  CubeState,
  CubeColor,
} from "../../cube-core/CubeState";

import { Corner } from "./Corner";
import { Edge } from "./Edge";

type ColorKey = CubeColor;

export class CubieCube {
  public cp: Corner[];
  public co: number[];

  public ep: Edge[];
  public eo: number[];

  constructor() {
    this.cp = [
      Corner.URF,
      Corner.UFL,
      Corner.ULB,
      Corner.UBR,
      Corner.DFR,
      Corner.DLF,
      Corner.DBL,
      Corner.DRB,
    ];

    this.co = [
      0, 0, 0, 0,
      0, 0, 0, 0,
    ];

    this.ep = [
      Edge.UF,
      Edge.UL,
      Edge.UB,
      Edge.UR,
      Edge.DF,
      Edge.DL,
      Edge.DB,
      Edge.DR,
      Edge.FR,
      Edge.FL,
      Edge.BL,
      Edge.BR,
    ];

    this.eo = [
      0, 0, 0, 0,
      0, 0, 0, 0,
      0, 0, 0, 0,
    ];
  }

  public clone(): CubieCube {
    const cube = new CubieCube();

    cube.cp = [...this.cp];
    cube.co = [...this.co];

    cube.ep = [...this.ep];
    cube.eo = [...this.eo];

    return cube;
  }

  public isSolved(): boolean {
    return (
      this.cp.every((corner, i) => corner === i) &&
      this.co.every((orientation) => orientation === 0) &&
      this.ep.every((edge, i) => edge === i) &&
      this.eo.every((orientation) => orientation === 0)
    );
  }

  public static fromCubeState(state: CubeState): CubieCube {
    const cube = new CubieCube();

    /*
    * Corner positions:
    *
    * URF, UFL, ULB, UBR,
    * DFR, DLF, DBL, DRB
    */
    const cornerColors: ColorKey[][] = [
      [state.U[8], state.R[0], state.F[2]], // URF
      [state.U[6], state.F[0], state.L[2]], // UFL
      [state.U[0], state.L[0], state.B[2]], // ULB
      [state.U[2], state.B[0], state.R[2]], // UBR

      [state.D[2], state.F[8], state.R[6]], // DFR
      [state.D[0], state.L[8], state.F[6]], // DLF
      [state.D[6], state.B[8], state.L[6]], // DBL
      [state.D[8], state.R[8], state.B[6]], // DRB
    ];

    /*
    * Solved colors for each corner cubie.
    *
    * The first color is always the U/D color.
    */
    const knownCorners: ColorKey[][] = [
      [CubeColor.White, CubeColor.Red, CubeColor.Green],    // URF
      [CubeColor.White, CubeColor.Green, CubeColor.Orange], // UFL
      [CubeColor.White, CubeColor.Orange, CubeColor.Blue],  // ULB
      [CubeColor.White, CubeColor.Blue, CubeColor.Red],     // UBR

      [CubeColor.Yellow, CubeColor.Green, CubeColor.Red],   // DFR
      [CubeColor.Yellow, CubeColor.Orange, CubeColor.Green],// DLF
      [CubeColor.Yellow, CubeColor.Blue, CubeColor.Orange], // DBL
      [CubeColor.Yellow, CubeColor.Red, CubeColor.Blue],    // DRB
    ];

    /*
    * Convert corners.
    */
    for (let position = 0; position < 8; position++) {
      const colors = cornerColors[position];

      let cubie = -1;

      /*
      * Identify the cubie by its three colors,
      * ignoring orientation.
      */
      for (let i = 0; i < 8; i++) {
        const known = knownCorners[i];

        if (
          colors.includes(known[0]) &&
          colors.includes(known[1]) &&
          colors.includes(known[2])
        ) {
          cubie = i;
          break;
        }
      }

      if (cubie === -1) {
        throw new Error(
          `Invalid corner at position ${position}: ${colors.join("")}`
        );
      }

      cube.cp[position] = cubie as Corner;

      /*
      * Corner orientation:
      *
      * 0 = U/D sticker is on the U/D face
      * 1 = U/D sticker is on the R/L face
      * 2 = U/D sticker is on the F/B face
      */
      const udColor =
        knownCorners[cubie][0];

      if (colors[0] === udColor) {
        cube.co[position] = 0;
      } else if (colors[1] === udColor) {
        cube.co[position] = 1;
      } else if (colors[2] === udColor) {
        cube.co[position] = 2;
      } else {
        throw new Error(
          `Invalid corner orientation at position ${position}: ${colors.join("")}`
        );
      }
    }

    /*
    * Edge positions.
    */
    const edgeColors: ColorKey[][] = [
      [state.U[7], state.F[1]], // UF
      [state.U[3], state.L[1]], // UL
      [state.U[1], state.B[1]], // UB
      [state.U[5], state.R[1]], // UR

      [state.D[1], state.F[7]], // DF
      [state.D[3], state.L[7]], // DL
      [state.D[7], state.B[7]], // DB
      [state.D[5], state.R[7]], // DR

      [state.F[5], state.R[3]], // FR
      [state.F[3], state.L[5]], // FL
      [state.B[5], state.L[3]], // BL
      [state.B[3], state.R[5]], // BR
    ];

    const knownEdges: ColorKey[][] = [
      [CubeColor.White, CubeColor.Green],  // UF
      [CubeColor.White, CubeColor.Orange], // UL
      [CubeColor.White, CubeColor.Blue],   // UB
      [CubeColor.White, CubeColor.Red],    // UR

      [CubeColor.Yellow, CubeColor.Green],  // DF
      [CubeColor.Yellow, CubeColor.Orange], // DL
      [CubeColor.Yellow, CubeColor.Blue],   // DB
      [CubeColor.Yellow, CubeColor.Red],    // DR

      [CubeColor.Green, CubeColor.Red],    // FR
      [CubeColor.Green, CubeColor.Orange], // FL
      [CubeColor.Blue, CubeColor.Orange],  // BL
      [CubeColor.Blue, CubeColor.Red],     // BR
    ];

    /*
    * Convert edges.
    */
    for (let position = 0; position < 12; position++) {
      const colors = edgeColors[position];

      let found = false;

      for (let edge = 0; edge < 12; edge++) {
        const known = knownEdges[edge];

        if (
          colors[0] === known[0] &&
          colors[1] === known[1]
        ) {
          cube.ep[position] = edge as Edge;
          cube.eo[position] = 0;
          found = true;
          break;
        }

        if (
          colors[0] === known[1] &&
          colors[1] === known[0]
        ) {
          cube.ep[position] = edge as Edge;
          cube.eo[position] = 1;
          found = true;
          break;
        }
      }

      if (!found) {
        throw new Error(
          `Invalid edge at position ${position}: ${colors.join("")}`
        );
      }
    }

    return cube;
  }
}