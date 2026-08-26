"""
CubeAI - Coach

Deterministic coaching layer for CubeAI.

The Coach does NOT:
    - detect cube stickers
    - classify colors
    - validate raw camera input
    - perform cube moves
    - solve the cube
    - convert CubeState <-> CubieState

Those responsibilities belong to the vision and engine layers.

The Coach receives a solver-generated algorithm and provides:

    1. Move explanations
    2. Algorithm explanations
    3. Step-by-step guidance
    4. Solving progress
    5. Mistake / deviation detection
    6. Cube orientation guidance
    7. Beginner-friendly tips

The implementation is deterministic and engine-aware.

Notation follows standard Rubik's Cube notation:

    U = Up
    R = Right
    F = Front
    D = Down
    L = Left
    B = Back

Modifiers:

    X  = clockwise quarter turn
    X' = counter-clockwise quarter turn
    X2 = 180-degree turn
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Iterable, Optional


# ============================================================================
# Paths
# ============================================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

ENGINE_DIR = os.path.abspath(
    os.path.join(
        CURRENT_DIR,
        "..",
        "engine",
    )
)

if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)


# ============================================================================
# Engine imports
# ============================================================================

try:
    from move import (
        Move,
        parse_algorithm,
        format_algorithm,
        simplify_moves,
    )
except ImportError as exc:
    Move = None
    parse_algorithm = None
    format_algorithm = None
    simplify_moves = None

    MOVE_IMPORT_ERROR = str(exc)

else:
    MOVE_IMPORT_ERROR = None


# ============================================================================
# Constants
# ============================================================================

FACE_NAMES = (
    "U",
    "R",
    "F",
    "D",
    "L",
    "B",
)

FACE_DESCRIPTIONS = {
    "U": "upper",
    "R": "right",
    "F": "front",
    "D": "down",
    "L": "left",
    "B": "back",
}

FACE_LONG_NAMES = {
    "U": "Up",
    "R": "Right",
    "F": "Front",
    "D": "Down",
    "L": "Left",
    "B": "Back",
}

FACE_COLORS = {
    "U": "white",
    "R": "red",
    "F": "green",
    "D": "yellow",
    "L": "orange",
    "B": "blue",
}


# ============================================================================
# Move explanation
# ============================================================================

@dataclass(frozen=True)
class MoveExplanation:
    """
    Human-readable explanation of a single cube move.
    """

    step: int
    notation: str
    face: str
    face_name: str
    direction: str
    quarter_turns: int
    description: str
    instruction: str
    tip: str

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "notation": self.notation,
            "face": self.face,
            "face_name": self.face_name,
            "direction": self.direction,
            "quarter_turns": self.quarter_turns,
            "description": self.description,
            "instruction": self.instruction,
            "tip": self.tip,
        }


# ============================================================================
# Coaching step
# ============================================================================

@dataclass(frozen=True)
class CoachingStep:
    """
    One step in a generated coaching sequence.
    """

    step: int
    total_steps: int
    move: MoveExplanation
    progress_before: float
    progress_after: float

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "total_steps": self.total_steps,
            "move": self.move.to_dict(),
            "progress_before": self.progress_before,
            "progress_after": self.progress_after,
        }


# ============================================================================
# Progress
# ============================================================================

@dataclass(frozen=True)
class SolvingProgress:
    """
    Represents progress through a solver-generated algorithm.
    """

    completed_moves: int
    total_moves: int
    remaining_moves: int
    percentage: float
    completed_algorithm: str
    remaining_algorithm: str
    solved: bool

    def to_dict(self) -> dict:
        return {
            "completed_moves": self.completed_moves,
            "total_moves": self.total_moves,
            "remaining_moves": self.remaining_moves,
            "percentage": self.percentage,
            "completed_algorithm": self.completed_algorithm,
            "remaining_algorithm": self.remaining_algorithm,
            "solved": self.solved,
        }


# ============================================================================
# Deviation result
# ============================================================================

@dataclass(frozen=True)
class DeviationResult:
    """
    Result of comparing a user's move against the expected move.
    """

    valid: bool
    expected: Optional[str]
    actual: Optional[str]
    message: str
    severity: str

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "expected": self.expected,
            "actual": self.actual,
            "message": self.message,
            "severity": self.severity,
        }


# ============================================================================
# Algorithm information
# ============================================================================

@dataclass(frozen=True)
class AlgorithmExplanation:
    """
    High-level explanation of an algorithm.
    """

    algorithm: str
    moves: int
    simplified: str
    faces_used: tuple[str, ...]
    contains_double_turns: bool
    contains_inverse_turns: bool
    description: str

    def to_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "moves": self.moves,
            "simplified": self.simplified,
            "faces_used": list(self.faces_used),
            "contains_double_turns": self.contains_double_turns,
            "contains_inverse_turns": self.contains_inverse_turns,
            "description": self.description,
        }


# ============================================================================
# Coach
# ============================================================================

class Coach:
    """
    Deterministic CubeAI coaching engine.

    Example:

        coach = Coach()

        guidance = coach.guide(
            "R U R' U'"
        )

        for step in guidance:
            print(step)
    """

    def __init__(
        self,
        algorithm: str | None = None,
    ) -> None:

        self.algorithm = ""
        self.moves: list[Move] = []
        self.current_step = 0

        if algorithm is not None:
            self.set_algorithm(
                algorithm
            )

    # ========================================================================
    # Validation
    # ========================================================================

    def _ensure_engine(self) -> None:

        if Move is None:

            raise RuntimeError(
                "CubeAI move engine could not be imported: "
                f"{MOVE_IMPORT_ERROR}"
            )

    # ========================================================================
    # Algorithm setup
    # ========================================================================

    def set_algorithm(
        self,
        algorithm: str,
    ) -> None:
        """
        Load a solver-generated algorithm.
        """

        self._ensure_engine()

        if not isinstance(
            algorithm,
            str,
        ):
            raise TypeError(
                "Algorithm must be a string."
            )

        self.algorithm = algorithm.strip()

        self.moves = parse_algorithm(
            self.algorithm
        )

        self.current_step = 0

    # ========================================================================
    # Reset
    # ========================================================================

    def reset(self) -> None:
        """
        Reset coaching progress.
        """

        self.current_step = 0

    # ========================================================================
    # Move explanation
    # ========================================================================

    def explain_move(
        self,
        move: Move | str,
        step: int = 1,
    ) -> MoveExplanation:
        """
        Explain one move in beginner-friendly language.
        """

        self._ensure_engine()

        if isinstance(
            move,
            str,
        ):
            move = Move.parse(
                move
            )

        if not isinstance(
            move,
            Move,
        ):
            raise TypeError(
                "move must be a Move or move notation string."
            )

        face = move.face
        notation = str(move)

        face_name = FACE_LONG_NAMES[
            face
        ]

        quarter_turns = (
            move.quarter_turns
        )

        if move.modifier == "":

            direction = "clockwise"

            description = (
                f"Turn the {face_name} face clockwise."
            )

            instruction = (
                f"Rotate the {face_descriptive_name(face)} "
                "one quarter turn clockwise."
            )

        elif move.modifier == "'":

            direction = "counter-clockwise"

            description = (
                f"Turn the {face_name} face counter-clockwise."
            )

            instruction = (
                f"Rotate the {face_descriptive_name(face)} "
                "one quarter turn counter-clockwise."
            )

        else:

            direction = "180-degree"

            description = (
                f"Turn the {face_name} face 180 degrees."
            )

            instruction = (
                f"Rotate the {face_descriptive_name(face)} "
                "half a turn."
            )

        tip = self._move_tip(
            move
        )

        return MoveExplanation(
            step=step,
            notation=notation,
            face=face,
            face_name=face_name,
            direction=direction,
            quarter_turns=quarter_turns,
            description=description,
            instruction=instruction,
            tip=tip,
        )

    # ========================================================================
    # Move tips
    # ========================================================================

    def _move_tip(
        self,
        move: Move,
    ) -> str:

        face = move.face

        if face == "U":

            return (
                "Keep the cube orientation fixed while turning "
                "the upper layer."
            )

        if face == "D":

            return (
                "Keep the cube orientation fixed while turning "
                "the bottom layer."
            )

        if face == "R":

            return (
                "Keep the front face pointing toward you "
                "while turning the right layer."
            )

        if face == "L":

            return (
                "Keep the front face pointing toward you "
                "while turning the left layer."
            )

        if face == "F":

            return (
                "Turn only the front face; do not rotate "
                "the entire cube."
            )

        if face == "B":

            return (
                "The back face is opposite the front. "
                "Do not rotate the entire cube to perform this move."
            )

        return ""

    # ========================================================================
    # Algorithm explanation
    # ========================================================================

    def explain_algorithm(
        self,
        algorithm: str | None = None,
    ) -> AlgorithmExplanation:
        """
        Explain the structure of an algorithm.
        """

        self._ensure_engine()

        if algorithm is None:
            algorithm = self.algorithm

        moves = parse_algorithm(
            algorithm
        )

        simplified_moves = simplify_moves(
            moves
        )

        simplified = format_algorithm(
            simplified_moves
        )

        faces = tuple(
            dict.fromkeys(
                move.face
                for move in moves
            )
        )

        contains_double_turns = any(
            move.modifier == "2"
            for move in moves
        )

        contains_inverse_turns = any(
            move.modifier == "'"
            for move in moves
        )

        if not moves:

            description = (
                "The algorithm contains no moves."
            )

        elif len(moves) == 1:

            description = (
                "This algorithm contains one cube move."
            )

        else:

            description = (
                f"This algorithm contains {len(moves)} moves "
                f"using {len(faces)} different faces."
            )

        return AlgorithmExplanation(
            algorithm=format_algorithm(moves),
            moves=len(moves),
            simplified=simplified,
            faces_used=faces,
            contains_double_turns=contains_double_turns,
            contains_inverse_turns=contains_inverse_turns,
            description=description,
        )

    # ========================================================================
    # Step-by-step guidance
    # ========================================================================

    def guide(
        self,
        algorithm: str | None = None,
    ) -> list[CoachingStep]:
        """
        Generate complete step-by-step guidance.
        """

        if algorithm is not None:
            self.set_algorithm(
                algorithm
            )

        total = len(
            self.moves
        )

        steps: list[CoachingStep] = []

        for index, move in enumerate(
            self.moves,
            start=1,
        ):

            explanation = self.explain_move(
                move,
                step=index,
            )

            before = (
                (index - 1)
                / total
                * 100
                if total
                else 100.0
            )

            after = (
                index
                / total
                * 100
                if total
                else 100.0
            )

            steps.append(
                CoachingStep(
                    step=index,
                    total_steps=total,
                    move=explanation,
                    progress_before=round(
                        before,
                        2,
                    ),
                    progress_after=round(
                        after,
                        2,
                    ),
                )
            )

        return steps

    # ========================================================================
    # Next step
    # ========================================================================

    def next_step(
        self,
    ) -> CoachingStep | None:
        """
        Return the next coaching step and advance progress.
        """

        if self.current_step >= len(
            self.moves
        ):
            return None

        index = (
            self.current_step + 1
        )

        move = self.moves[
            self.current_step
        ]

        total = len(
            self.moves
        )

        explanation = self.explain_move(
            move,
            step=index,
        )

        before = (
            self.current_step
            / total
            * 100
            if total
            else 100.0
        )

        after = (
            index
            / total
            * 100
            if total
            else 100.0
        )

        self.current_step += 1

        return CoachingStep(
            step=index,
            total_steps=total,
            move=explanation,
            progress_before=round(
                before,
                2,
            ),
            progress_after=round(
                after,
                2,
            ),
        )

    # ========================================================================
    # Progress
    # ========================================================================

    def progress(
        self,
    ) -> SolvingProgress:

        total = len(
            self.moves
        )

        completed = min(
            self.current_step,
            total,
        )

        remaining = (
            total - completed
        )

        percentage = (
            completed / total * 100
            if total
            else 100.0
        )

        completed_algorithm = format_algorithm(
            self.moves[
                :completed
            ]
        )

        remaining_algorithm = format_algorithm(
            self.moves[
                completed:
            ]
        )

        return SolvingProgress(
            completed_moves=completed,
            total_moves=total,
            remaining_moves=remaining,
            percentage=round(
                percentage,
                2,
            ),
            completed_algorithm=completed_algorithm,
            remaining_algorithm=remaining_algorithm,
            solved=(
                total == 0
                or completed == total
            ),
        )

    # ========================================================================
    # Deviation detection
    # ========================================================================

    def check_move(
        self,
        actual_move: Move | str,
    ) -> DeviationResult:
        """
        Compare a user's move against the expected next move.

        This checks notation-level deviation.

        It does not attempt to infer a physical move from
        camera data. That belongs to the vision layer.
        """

        if isinstance(
            actual_move,
            str,
        ):

            actual_move = Move.parse(
                actual_move
            )

        if not isinstance(
            actual_move,
            Move,
        ):
            raise TypeError(
                "actual_move must be a Move or move notation string."
            )

        if self.current_step >= len(
            self.moves
        ):

            return DeviationResult(
                valid=False,
                expected=None,
                actual=str(actual_move),
                message=(
                    "The solution is already complete. "
                    "No more moves are expected."
                ),
                severity="info",
            )

        expected = self.moves[
            self.current_step
        ]

        if str(actual_move) == str(expected):

            self.current_step += 1

            if self.current_step == len(
                self.moves
            ):

                message = (
                    "Correct. The solution is complete."
                )

            else:

                message = (
                    f"Correct. Next move: "
                    f"{self.moves[self.current_step]}."
                )

            return DeviationResult(
                valid=True,
                expected=str(expected),
                actual=str(actual_move),
                message=message,
                severity="success",
            )

        # Same face but wrong modifier.
        if actual_move.face == expected.face:

            return DeviationResult(
                valid=False,
                expected=str(expected),
                actual=str(actual_move),
                message=(
                    f"You're on the correct face, but the turn "
                    f"should be {expected}, not {actual_move}."
                ),
                severity="warning",
            )

        return DeviationResult(
            valid=False,
            expected=str(expected),
            actual=str(actual_move),
            message=(
                f"Expected {expected}, but you performed "
                f"{actual_move}. Keep the cube orientation fixed "
                f"and follow the solution sequence."
            ),
            severity="error",
        )

    # ========================================================================
    # Orientation guidance
    # ========================================================================

    def orientation_guidance(
        self,
    ) -> dict:

        return {
            "fixed_orientation": True,
            "instruction": (
                "Keep the cube orientation fixed throughout "
                "the algorithm unless the solver explicitly "
                "requires a cube rotation."
            ),
            "front": "Green",
            "back": "Blue",
            "up": "White",
            "down": "Yellow",
            "right": "Red",
            "left": "Orange",
            "tip": (
                "Do not rotate the entire cube between moves. "
                "A move such as R means the right face relative "
                "to your current cube orientation."
            ),
        }

    # ========================================================================
    # Beginner tips
    # ========================================================================

    def beginner_tips(
        self,
        move: Move | str | None = None,
    ) -> list[str]:

        tips = [
            (
                "Keep the cube orientation fixed while "
                "following a solution."
            ),
            (
                "A prime symbol (') means turn the face "
                "counter-clockwise."
            ),
            (
                "A 2 means turn the face 180 degrees."
            ),
            (
                "Do not confuse rotating a face with rotating "
                "the entire cube."
            ),
            (
                "Read the solution from left to right and "
                "perform one move at a time."
            ),
        ]

        if move is not None:

            if isinstance(
                move,
                str,
            ):
                move = Move.parse(
                    move
                )

            if move.modifier == "'":

                tips.append(
                    "Remember: the prime symbol means "
                    "counter-clockwise."
                )

            elif move.modifier == "2":

                tips.append(
                    "For a 180-degree turn, rotate the face "
                    "halfway around."
                )

        return tips

    # ========================================================================
    # Completion
    # ========================================================================

    def is_complete(
        self,
    ) -> bool:

        return (
            self.current_step
            >= len(self.moves)
        )

    # ========================================================================
    # Full coaching session
    # ========================================================================

    def session(
        self,
        algorithm: str | None = None,
    ) -> dict:
        """
        Generate the complete coaching payload.

        This is useful later for an API endpoint.
        """

        if algorithm is not None:
            self.set_algorithm(
                algorithm
            )

        explanation = self.explain_algorithm()

        steps = self.guide()

        return {
            "algorithm": explanation.to_dict(),
            "orientation": self.orientation_guidance(),
            "tips": self.beginner_tips(),
            "steps": [
                step.to_dict()
                for step in steps
            ],
            "progress": self.progress().to_dict(),
        }


# ============================================================================
# Helper
# ============================================================================

def face_descriptive_name(
    face: str,
) -> str:

    descriptions = {
        "U": "upper",
        "R": "right",
        "F": "front",
        "D": "down",
        "L": "left",
        "B": "back",
    }

    return descriptions.get(
        face,
        face,
    )


# ============================================================================
# Tests
# ============================================================================

def _test_move_explanation() -> bool:

    coach = Coach()

    tests = (
        ("R", "clockwise"),
        ("R'", "counter-clockwise"),
        ("R2", "180-degree"),
        ("U", "clockwise"),
        ("F'", "counter-clockwise"),
    )

    passed = True

    print(
        "Move explanation tests:"
    )

    for notation, expected_direction in tests:

        explanation = coach.explain_move(
            notation
        )

        result = (
            explanation.direction
            == expected_direction
        )

        print(
            f"  {notation}: "
            f"{'PASS' if result else 'FAIL'}"
        )

        if not result:
            passed = False

    print()

    return passed


def _test_algorithm_explanation() -> bool:

    coach = Coach()

    explanation = coach.explain_algorithm(
        "R U R' U' F2"
    )

    passed = (
        explanation.moves == 5
        and explanation.contains_double_turns
        and explanation.contains_inverse_turns
        and explanation.faces_used
        == ("R", "U", "F")
    )

    print(
        "Algorithm explanation test:",
        "PASS" if passed else "FAIL",
    )

    print()

    return passed


def _test_step_guidance() -> bool:

    coach = Coach(
        "R U R' U'"
    )

    steps = coach.guide()

    passed = (
        len(steps) == 4
        and steps[0].move.notation == "R"
        and steps[1].move.notation == "U"
        and steps[2].move.notation == "R'"
        and steps[3].move.notation == "U'"
        and steps[-1].progress_after == 100.0
    )

    print(
        "Step-by-step guidance test:",
        "PASS" if passed else "FAIL",
    )

    print()

    return passed


def _test_progress() -> bool:

    coach = Coach(
        "R U R' U'"
    )

    initial = coach.progress()

    first = coach.next_step()

    middle = coach.progress()

    coach.next_step()
    coach.next_step()
    coach.next_step()

    final = coach.progress()

    passed = (
        initial.completed_moves == 0
        and initial.percentage == 0.0
        and first is not None
        and middle.completed_moves == 1
        and final.completed_moves == 4
        and final.percentage == 100.0
        and final.solved
    )

    print(
        "Solving progress test:",
        "PASS" if passed else "FAIL",
    )

    print()

    return passed


def _test_deviation_detection() -> bool:

    coach = Coach(
        "R U R' U'"
    )

    correct = coach.check_move(
        "R"
    )

    wrong_face = coach.check_move(
        "F"
    )

    correct_again = coach.check_move(
        "U"
    )

    passed = (
        correct.valid
        and not wrong_face.valid
        and correct_again.valid
    )

    print(
        "Deviation detection test:",
        "PASS" if passed else "FAIL",
    )

    print()

    return passed


def _test_orientation_guidance() -> bool:

    coach = Coach()

    guidance = (
        coach.orientation_guidance()
    )

    passed = (
        guidance["fixed_orientation"]
        and guidance["front"] == "Green"
        and guidance["up"] == "White"
        and guidance["right"] == "Red"
    )

    print(
        "Orientation guidance test:",
        "PASS" if passed else "FAIL",
    )

    print()

    return passed


def _test_session() -> bool:

    coach = Coach()

    session = coach.session(
        "R U R' U'"
    )

    passed = (
        "algorithm" in session
        and "orientation" in session
        and "tips" in session
        and "steps" in session
        and "progress" in session
        and len(session["steps"]) == 4
    )

    print(
        "Full coaching session test:",
        "PASS" if passed else "FAIL",
    )

    print()

    return passed


# ============================================================================
# Demonstration
# ============================================================================

def _demo() -> None:

    print(
        "========================================"
    )

    print(
        "CubeAI Coach"
    )

    print(
        "========================================"
    )

    algorithm = (
        "R U R' U' F2 L D"
    )

    coach = Coach(
        algorithm
    )

    print()

    # ------------------------------------------------------------------------
    # Algorithm
    # ------------------------------------------------------------------------

    explanation = coach.explain_algorithm()

    print(
        "Algorithm:"
    )

    print(
        f"  {explanation.algorithm}"
    )

    print(
        f"Moves: {explanation.moves}"
    )

    print(
        f"Simplified: {explanation.simplified}"
    )

    print(
        f"Faces used: "
        f"{', '.join(explanation.faces_used)}"
    )

    print(
        f"Description: "
        f"{explanation.description}"
    )

    print()

    # ------------------------------------------------------------------------
    # Orientation
    # ------------------------------------------------------------------------

    print(
        "Cube orientation:"
    )

    orientation = (
        coach.orientation_guidance()
    )

    print(
        f"  Front: {orientation['front']}"
    )

    print(
        f"  Back:  {orientation['back']}"
    )

    print(
        f"  Up:    {orientation['up']}"
    )

    print(
        f"  Down:  {orientation['down']}"
    )

    print(
        f"  Right: {orientation['right']}"
    )

    print(
        f"  Left:  {orientation['left']}"
    )

    print(
        f"  Tip:   {orientation['tip']}"
    )

    print()

    # ------------------------------------------------------------------------
    # Step-by-step
    # ------------------------------------------------------------------------

    print(
        "Step-by-step guidance:"
    )

    for step in coach.guide():

        move = step.move

        print()

        print(
            f"  Step {step.step}/{step.total_steps}"
        )

        print(
            f"  Move: {move.notation}"
        )

        print(
            f"  {move.description}"
        )

        print(
            f"  {move.instruction}"
        )

        print(
            f"  Tip: {move.tip}"
        )

        print(
            f"  Progress: "
            f"{step.progress_after:.0f}%"
        )

    print()

    # ------------------------------------------------------------------------
    # Progress
    # ------------------------------------------------------------------------

    print(
        "Progress:"
    )

    progress = coach.progress()

    print(
        f"  Completed: "
        f"{progress.completed_moves}/"
        f"{progress.total_moves}"
    )

    print(
        f"  Remaining: "
        f"{progress.remaining_moves}"
    )

    print(
        f"  Percentage: "
        f"{progress.percentage}%"
    )

    print()

    # ------------------------------------------------------------------------
    # Deviation example
    # ------------------------------------------------------------------------

    coach.reset()

    print(
        "Deviation detection:"
    )

    result = coach.check_move(
        "F"
    )

    print(
        f"  Expected: "
        f"{result.expected}"
    )

    print(
        f"  Actual:   "
        f"{result.actual}"
    )

    print(
        f"  Valid:    "
        f"{result.valid}"
    )

    print(
        f"  Severity: "
        f"{result.severity}"
    )

    print(
        f"  Message:  "
        f"{result.message}"
    )

    print()

    print(
        "========================================"
    )


# ============================================================================
# Main
# ============================================================================

def main() -> None:

    print(
        "CubeAI Coach"
    )

    print(
        "------------------"
    )

    print()

    test_results = (
        _test_move_explanation(),
        _test_algorithm_explanation(),
        _test_step_guidance(),
        _test_progress(),
        _test_deviation_detection(),
        _test_orientation_guidance(),
        _test_session(),
    )

    all_passed = all(
        test_results
    )

    print(
        "========================================"
    )

    print(
        "Coach tests:",
        "PASS" if all_passed else "FAILED",
    )

    print(
        "========================================"
    )

    if all_passed:

        print()

        _demo()


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    main()