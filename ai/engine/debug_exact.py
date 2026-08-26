"""
Run this in cube-ai/ai/engine/ to see exactly which stickers differ
after an R move round-trip.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cubeState import CubeState, FACE_TO_COLOR, FACE_NAMES
from cubie import CubieState, CornerCubie, EdgeCubie
from cubeValidator import (
    CubeValidator, CORNER_FACELETS, EDGE_FACELETS,
    CORNER_COLORS as VAL_CORNER_COLORS,
    EDGE_COLORS   as VAL_EDGE_COLORS,
)
from move import apply_algorithm

FACE_NAMES_T = ("U", "R", "F", "D", "L", "B")

def create_solved_cubestate():
    return CubeState({
        face: [[color]*3 for _ in range(3)]
        for face, color in FACE_TO_COLOR.items()
    })

def corner_orientation(colors, facelets):
    ud = next((i for i,c in enumerate(colors) if c in ("white","yellow")), -1)
    if ud == -1: return 0
    return ud if facelets[0][0]=="U" else (-ud)%3

def edge_orientation(colors, facelets):
    faces = (facelets[0][0], facelets[1][0])
    if "white" in colors or "yellow" in colors:
        t = "white" if "white" in colors else "yellow"
        for c,f in zip(colors, faces):
            if c==t and f in ("U","D"): return 0
        return 1
    if "green" in colors or "blue" in colors:
        t = "green" if "green" in colors else "blue"
        for c,f in zip(colors, faces):
            if c==t and f in ("F","B"): return 0
        return 1
    return 1

def cubestate_to_cubiestate(cube):
    corners = []
    for slot_idx, facelets in enumerate(CORNER_FACELETS):
        colors = [str(cube.faces[face][row][col]).lower() for face,row,col in facelets]
        cs = frozenset(colors)
        piece_idx = VAL_CORNER_COLORS.index(cs)
        orient = corner_orientation(colors, facelets)
        corners.append(CornerCubie(piece=piece_idx, orientation=orient))
    edges = []
    for slot_idx, facelets in enumerate(EDGE_FACELETS):
        colors = [str(cube.faces[face][row][col]).lower() for face,row,col in facelets]
        cs = frozenset(colors)
        piece_idx = VAL_EDGE_COLORS.index(cs)
        orient = edge_orientation(colors, facelets)
        edges.append(EdgeCubie(piece=piece_idx, orientation=orient))
    return CubieState(corners=corners, edges=edges)

# Build geometry-based canonical
CORNER_PIECE_CANONICAL = tuple(
    tuple(FACE_TO_COLOR[face] for face,_,_ in facelets)
    for facelets in CORNER_FACELETS
)
EDGE_PIECE_CANONICAL = tuple(
    tuple(FACE_TO_COLOR[face] for face,_,_ in facelets)
    for facelets in EDGE_FACELETS
)

CORNER_PERM_TABLE = {
    (False,False,0):(0,1,2),(False,False,1):(2,0,1),(False,False,2):(1,2,0),
    (False,True, 0):(0,2,1),(False,True, 1):(2,1,0),(False,True, 2):(1,0,2),
    (True, False,0):(0,2,1),(True, False,1):(1,0,2),(True, False,2):(2,1,0),
    (True, True, 0):(0,1,2),(True, True, 1):(1,2,0),(True, True, 2):(2,0,1),
}

def cubiestate_to_cubestate(cubie):
    faces = {face: [[""] * 3 for _ in range(3)] for face in FACE_NAMES_T}
    for face, color in FACE_TO_COLOR.items():
        faces[face][1][1] = color
    for slot_idx, facelets in enumerate(CORNER_FACELETS):
        corner = cubie.corners[slot_idx]
        canonical = CORNER_PIECE_CANONICAL[corner.piece]
        perm = CORNER_PERM_TABLE[(corner.piece>=4, facelets[0][0]=="D", corner.orientation)]
        rotated = (canonical[perm[0]], canonical[perm[1]], canonical[perm[2]])
        for (face,row,col), color in zip(facelets, rotated):
            faces[face][row][col] = color
    for slot_idx, facelets in enumerate(EDGE_FACELETS):
        edge = cubie.edges[slot_idx]
        ce = EDGE_PIECE_CANONICAL[edge.piece]
        rotated = (ce[edge.orientation], ce[1-edge.orientation])
        for (face,row,col), color in zip(facelets, rotated):
            faces[face][row][col] = color
    return CubeState(faces)

# Test R move
solved = create_solved_cubestate()
scrambled = apply_algorithm(solved, "R")
cubie_state = cubestate_to_cubiestate(scrambled)
restored = cubiestate_to_cubestate(cubie_state)

print("=== R move round-trip debug ===")
print()
print("Scrambled (expected):")
for face in FACE_NAMES_T:
    for row in scrambled.faces[face]:
        print(f"  {face}: {row}")
print()
print("Restored (got):")
for face in FACE_NAMES_T:
    for row in restored.faces[face]:
        print(f"  {face}: {row}")
print()
print("Differences:")
diffs = []
for face in FACE_NAMES_T:
    for r in range(3):
        for c in range(3):
            a = scrambled.faces[face][r][c]
            b = restored.faces[face][r][c]
            if a != b:
                diffs.append(f"  {face}[{r}][{c}]: expected={a} got={b}")
if diffs:
    for d in diffs:
        print(d)
else:
    print("  NONE - PASS!")

print()
print("=== CubieState after R ===")
print("Corners:")
CNAMES = ("UFR","URB","UBL","ULF","DFR","DRB","DBL","DLF")
for i,c in enumerate(cubie_state.corners):
    print(f"  slot {CNAMES[i]}: piece={c.piece}({CNAMES[c.piece]}) orient={c.orientation}")
print("Edges:")
ENAMES = ("UF","UR","UB","UL","FR","RB","BL","LF","DF","DR","DB","DL")
for i,e in enumerate(cubie_state.edges):
    print(f"  slot {ENAMES[i]}: piece={e.piece}({ENAMES[e.piece]}) orient={e.orientation}")

print()
print("=== Reconstruction trace for changed corners ===")
for slot_idx, facelets in enumerate(CORNER_FACELETS):
    corner = cubie_state.corners[slot_idx]
    if corner.piece == slot_idx and corner.orientation == 0:
        continue  # unchanged
    canonical = CORNER_PIECE_CANONICAL[corner.piece]
    perm = CORNER_PERM_TABLE[(corner.piece>=4, facelets[0][0]=="D", corner.orientation)]
    rotated = [canonical[perm[j]] for j in range(3)]
    expected = [scrambled.faces[face][row][col] for face,row,col in facelets]
    match = rotated == expected
    print(f"Slot {CNAMES[slot_idx]}: piece={CNAMES[corner.piece]} orient={corner.orientation}")
    print(f"  canonical={canonical}  perm={perm}")
    print(f"  rotated  ={rotated}")
    print(f"  expected ={expected}  {'OK' if match else 'WRONG'}")