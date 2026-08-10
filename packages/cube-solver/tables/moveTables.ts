import { Move } from "../../cube-core/Move";
import { Corner } from "../representation/Corner";
import { Edge } from "../representation/Edge";
import { CubieCube } from "../representation/CubieCube";

export interface CubieMove {
  cp: Corner[];
  co: number[];

  ep: Edge[];
  eo: number[];
}

/*
 * Only the six basic face turns are defined here initially.
 *
 * U  D  R  L  F  B
 *
 * U2, D2, R2, L2, F2, B2
 * and inverse moves are generated below.
 */

export const MOVE_TABLES: Partial<Record<Move, CubieMove>> = {
  U: {
    cp: [
      Corner.UBR,
      Corner.URF,
      Corner.UFL,
      Corner.ULB,
      Corner.DFR,
      Corner.DLF,
      Corner.DBL,
      Corner.DRB,
    ],

    co: [
      0, 0, 0, 0,
      0, 0, 0, 0,
    ],

    ep: [
      Edge.UR,
      Edge.UF,
      Edge.UL,
      Edge.UB,
      Edge.DF,
      Edge.DL,
      Edge.DB,
      Edge.DR,
      Edge.FR,
      Edge.FL,
      Edge.BL,
      Edge.BR,
    ],

    eo: [
      0, 0, 0, 0,
      0, 0, 0, 0,
      0, 0, 0, 0,
    ],
  },

  D: {
    cp: [
      Corner.URF,
      Corner.UFL,
      Corner.ULB,
      Corner.UBR,
      Corner.DLF,
      Corner.DBL,
      Corner.DRB,
      Corner.DFR,
    ],

    co: [
      0, 0, 0, 0,
      0, 0, 0, 0,
    ],

    ep: [
      Edge.UF,
      Edge.UL,
      Edge.UB,
      Edge.UR,
      Edge.DL,
      Edge.DB,
      Edge.DR,
      Edge.DF,
      Edge.FR,
      Edge.FL,
      Edge.BL,
      Edge.BR,
    ],

    eo: [
      0, 0, 0, 0,
      0, 0, 0, 0,
      0, 0, 0, 0,
    ],
  },

  R: {
    cp: [
      Corner.UBR,
      Corner.UFL,
      Corner.ULB,
      Corner.DRB,
      Corner.URF,
      Corner.DLF,
      Corner.DBL,
      Corner.DFR,
    ],

    co: [
      2, 0, 0, 1,
      1, 0, 0, 2,
    ],

    ep: [
      Edge.UF,
      Edge.UL,
      Edge.UB,
      Edge.BR,
      Edge.DF,
      Edge.DL,
      Edge.DB,
      Edge.FR,
      Edge.UR,
      Edge.FL,
      Edge.BL,
      Edge.DR,
    ],

    eo: [
      0, 0, 0, 0,
      0, 0, 0, 0,
      0, 0, 0, 0,
    ],
  },

  L: {
    cp: [
      Corner.URF,
      Corner.DLF,
      Corner.UFL,
      Corner.UBR,
      Corner.DFR,
      Corner.DBL,
      Corner.ULB,
      Corner.DRB,
    ],

    co: [
      0, 1, 2, 0,
      0, 2, 1, 0,
    ],

    ep: [
      Edge.UF,
      Edge.FL,
      Edge.UB,
      Edge.UR,
      Edge.DF,
      Edge.BL,
      Edge.DB,
      Edge.DR,
      Edge.FR,
      Edge.DL,
      Edge.UL,
      Edge.BR,
    ],

    eo: [
      0, 0, 0, 0,
      0, 0, 0, 0,
      0, 0, 0, 0,
    ],
  },

  F: {
    cp: [
      Corner.UFL,
      Corner.DLF,
      Corner.ULB,
      Corner.UBR,
      Corner.URF,
      Corner.DFR,
      Corner.DBL,
      Corner.DRB,
    ],

    co: [
      1, 2, 0, 0,
      2, 1, 0, 0,
    ],

    ep: [
      Edge.FL,
      Edge.UL,
      Edge.UB,
      Edge.UR,
      Edge.FR,
      Edge.DL,
      Edge.DB,
      Edge.DR,
      Edge.UF,
      Edge.DF,
      Edge.BL,
      Edge.BR,
    ],

    eo: [
      1, 0, 0, 0,
      1, 0, 0, 0,
      1, 1, 0, 0,
    ],
  },

  B: {
    cp: [
      Corner.URF,
      Corner.UFL,
      Corner.DBL,
      Corner.ULB,
      Corner.DFR,
      Corner.DLF,
      Corner.DRB,
      Corner.UBR,
    ],

    co: [
      0, 0, 1, 2,
      0, 0, 2, 1,
    ],

    ep: [
      Edge.UF,
      Edge.UL,
      Edge.BL,
      Edge.UR,
      Edge.DF,
      Edge.DL,
      Edge.BR,
      Edge.DR,
      Edge.FR,
      Edge.FL,
      Edge.DB,
      Edge.UB,
    ],

    eo: [
      0, 0, 1, 0,
      0, 0, 1, 0,
      0, 0, 1, 1,
    ],
  },
};


/*
 * ---------------------------------------------------------
 * Generate double moves
 * ---------------------------------------------------------
 */

MOVE_TABLES.U2 = composeMoves(
  MOVE_TABLES.U!,
  MOVE_TABLES.U!
);

MOVE_TABLES.D2 = composeMoves(
  MOVE_TABLES.D!,
  MOVE_TABLES.D!
);

MOVE_TABLES.R2 = composeMoves(
  MOVE_TABLES.R!,
  MOVE_TABLES.R!
);

MOVE_TABLES.L2 = composeMoves(
  MOVE_TABLES.L!,
  MOVE_TABLES.L!
);

MOVE_TABLES.F2 = composeMoves(
  MOVE_TABLES.F!,
  MOVE_TABLES.F!
);

MOVE_TABLES.B2 = composeMoves(
  MOVE_TABLES.B!,
  MOVE_TABLES.B!
);


/*
 * ---------------------------------------------------------
 * Generate inverse moves
 * ---------------------------------------------------------
 *
 * X' = X2 + X
 *
 * Example:
 *
 * R' = R R R
 */

MOVE_TABLES["U'"] = composeMoves(
  MOVE_TABLES.U2!,
  MOVE_TABLES.U!
);

MOVE_TABLES["D'"] = composeMoves(
  MOVE_TABLES.D2!,
  MOVE_TABLES.D!
);

MOVE_TABLES["R'"] = composeMoves(
  MOVE_TABLES.R2!,
  MOVE_TABLES.R!
);

MOVE_TABLES["L'"] = composeMoves(
  MOVE_TABLES.L2!,
  MOVE_TABLES.L!
);

MOVE_TABLES["F'"] = composeMoves(
  MOVE_TABLES.F2!,
  MOVE_TABLES.F!
);

MOVE_TABLES["B'"] = composeMoves(
  MOVE_TABLES.B2!,
  MOVE_TABLES.B!
);


/*
 * ---------------------------------------------------------
 * Compose two cubie moves
 * ---------------------------------------------------------
 */

function composeMoves(
  a: CubieMove,
  b: CubieMove
): CubieMove {
  const cp: Corner[] = new Array(8);
  const co: number[] = new Array(8);

  const ep: Edge[] = new Array(12);
  const eo: number[] = new Array(12);

  /*
   * Corners
   */

  for (let i = 0; i < 8; i++) {
    cp[i] = a.cp[b.cp[i]];

    co[i] =
      (a.co[b.cp[i]] + b.co[i]) % 3;
  }

  /*
   * Edges
   */

  for (let i = 0; i < 12; i++) {
    ep[i] = a.ep[b.ep[i]];

    eo[i] =
      (a.eo[b.ep[i]] + b.eo[i]) % 2;
  }

  return {
    cp,
    co,
    ep,
    eo,
  };
}


/*
 * ---------------------------------------------------------
 * Apply a cubie move
 * ---------------------------------------------------------
 */

export function applyCubieMove(
  cube: CubieCube,
  move: Move
): CubieCube {
  const table = MOVE_TABLES[move];

  if (!table) {
    throw new Error(
      `Unsupported move: ${move}`
    );
  }

  const result = cube.clone();

  /*
   * Corners
   */

  for (let i = 0; i < 8; i++) {
    result.cp[i] =
      cube.cp[table.cp[i]];

    result.co[i] =
      (
        cube.co[table.cp[i]] +
        table.co[i]
      ) % 3;
  }

  /*
   * Edges
   */

  for (let i = 0; i < 12; i++) {
    result.ep[i] =
      cube.ep[table.ep[i]];

    result.eo[i] =
      (
        cube.eo[table.ep[i]] +
        table.eo[i]
      ) % 2;
  }

  return result;
}