"""
CubeAI - Scan Session Test

Tests the connection between:

    CubeScanner
        ↓
    ScanResult
        ↓
    CubeScanSession
"""

import cv2

from ai.vision.scanner import CubeScanner
from ai.vision.scanSession import CubeScanSession


IMAGE_PATH = "test-images/cube-color.jpg"


def main() -> None:

    print("CubeAI Scan Session Test")
    print("------------------------")
    print()

    # ========================================================================
    # Create scanner and session
    # ========================================================================

    scanner = CubeScanner()
    session = CubeScanSession(
        scanner=scanner
    )

    print("Session created.")
    print()

    # ========================================================================
    # Load test image
    # ========================================================================

    print(
        f"Loading image: {IMAGE_PATH}"
    )

    image = cv2.imread(
        IMAGE_PATH,
        cv2.IMREAD_COLOR,
    )

    if image is None:

        print(
            "ERROR: Could not load image."
        )

        return

    print(
        f"Image loaded: "
        f"{image.shape[1]}x{image.shape[0]}"
    )

    print()

    # ========================================================================
    # Scan image
    # ========================================================================

    print("Scanning face...")
    print()

    result = scanner.scan(
        image
    )

    # ========================================================================
    # Display scan result
    # ========================================================================

    print()

    if not result.success:

        print("Face scan failed.")

        print(
            f"Error: {result.error}"
        )

        return

    print(
        "Face scan successful!"
    )

    print(
        f"  Face:       {result.face_name}"
    )

    print(
        f"  Color:      {result.face_color}"
    )

    print(
        f"  Confidence: {result.confidence:.2f}"
    )

    print()

    # ========================================================================
    # Add ScanResult to session
    # ========================================================================

    print(
        "Adding scan to session..."
    )

    accepted = session.add_scan(
        result
    )

    print(
        f"  Accepted: {accepted}"
    )

    print()

    # ========================================================================
    # Display session state
    # ========================================================================

    print(
        "Session state:"
    )

    print(
        f"  Scanned: "
        f"{session.scanned_count()}/6"
    )

    print(
        f"  Faces:   "
        f"{' '.join(session.scanned_faces())}"
    )

    print(
        f"  Missing: "
        f"{' '.join(session.missing_faces())}"
    )

    print()

    # ========================================================================
    # Build partial result
    # ========================================================================

    session_result = (
        session.build_result()
    )

    print(
        "Session result:"
    )

    print(
        f"  Complete:   "
        f"{session_result.success}"
    )

    print(
        f"  Confidence: "
        f"{session_result.confidence:.2f}"
    )

    print(
        f"  Scanned:    "
        f"{session_result.scanned_faces}"
    )

    print(
        f"  Missing:    "
        f"{session_result.missing_faces}"
    )

    print(
        f"  Error:      "
        f"{session_result.error}"
    )

    print()

    # ========================================================================
    # Display stored U face
    # ========================================================================

    if "U" in session_result.faces:

        print(
            "Stored U face:"
        )

        for row in session_result.faces["U"]:

            print(
                "  " + " ".join(row)
            )

        print()

    # ========================================================================
    # Final status
    # ========================================================================

    print(
        "Test complete."
    )


if __name__ == "__main__":
    main()