"""Adapters between API cube states and the Python engine representation."""

import sys
from pathlib import Path
from typing import Any

from ..models import CubeStateModel, StickerCubeStateModel

ENGINE_DIR = Path(__file__).resolve().parents[3] / "ai" / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from cubeState import CubeState
from cubie import CornerCubie, CubieState, EdgeCubie
from cubieConverter import cubiestate_to_cubestate, cubestate_to_cubiestate

FACE_NAMES = ("U", "R", "F", "D", "L", "B")
COLOR_NAMES = {
    "W": "white",
    "Y": "yellow",
    "R": "red",
    "O": "orange",
    "G": "green",
    "B": "blue",
    "WHITE": "white",
    "YELLOW": "yellow",
    "RED": "red",
    "ORANGE": "orange",
    "GREEN": "green",
    "BLUE": "blue",
}


def to_cubie_state(state: CubeStateModel | StickerCubeStateModel) -> CubieState:
    """Convert either API facelets or cubie arrays to validated engine cubies."""
    if isinstance(state, StickerCubeStateModel):
        normalized_faces = {
            face: [
                [COLOR_NAMES[str(color).upper()] for color in row]
                for row in state.faces[face]
            ]
            for face in FACE_NAMES
        }
        engine_cube = CubeState(faces=normalized_faces)
        if not engine_cube.is_complete():
            raise ValueError("Cube state has unknown stickers")
        cubies = cubestate_to_cubiestate(engine_cube)
    else:
        cubies = CubieState(
            corners=[
                CornerCubie(piece=piece, orientation=orientation)
                for piece, orientation in zip(
                    state.corners,
                    state.corner_orientations,
                )
            ],
            edges=[
                EdgeCubie(piece=piece, orientation=orientation)
                for piece, orientation in zip(
                    state.edges,
                    state.edge_orientations,
                )
            ],
        )

    validation = cubies.validate()
    if not validation["valid"]:
        raise ValueError("; ".join(validation["errors"]))
    return cubies


def to_api_cube_state(cubies: CubieState) -> CubeStateModel:
    """Convert engine cubies to the stable REST cubie-array contract."""
    return CubeStateModel(
        corners=[corner.piece for corner in cubies.corners],
        corner_orientations=[corner.orientation for corner in cubies.corners],
        edges=[edge.piece for edge in cubies.edges],
        edge_orientations=[edge.orientation for edge in cubies.edges],
    )


def to_engine_cube(state: CubeStateModel | StickerCubeStateModel) -> CubeState:
    """Convert an API state to the engine's color-face representation."""
    return cubies_to_engine_cube(to_cubie_state(state))


def cubies_to_engine_cube(cubies: CubieState) -> CubeState:
    """Convert an already-validated cubie state to sticker faces."""
    return cubiestate_to_cubestate(cubies)


def to_face_map(cube: CubeState) -> dict[str, list[list[str]]]:
    """Return the six faces in row-major order for frontend rendering."""
    return {
        face: [list(row) for row in cube.faces[face]]
        for face in FACE_NAMES
    }
